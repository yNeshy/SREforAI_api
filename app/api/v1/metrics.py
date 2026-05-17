"""
Metrics endpoints for cost monitoring and analytics.
All endpoints enforce strict tenant isolation via org_id filtering.
"""

from datetime import datetime
from typing import List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func, and_
from app.core.database import get_db
from app.models.usage_cache import HourlyDailyUsageCache
from app.api.schemas import (
    MetricsSummaryRequest,
    MetricsSummaryResponse,
    MetricsBreakdownRequest,
    MetricsBreakdownResponse,
    MetricsBreakdownItem,
    LeakDetectorResponse,
    LeakDetectorInsight,
    OrganizationContext
)
from app.api.dependencies import get_current_org

router = APIRouter()


@router.get("/summary", response_model=MetricsSummaryResponse)
async def get_metrics_summary(
    start_date: datetime,
    end_date: datetime,
    org_context: OrganizationContext = Depends(get_current_org),
    db: Session = Depends(get_db)
):
    """
    Get high-level card metrics for the authenticated organization.
    
    This endpoint:
    - Calculates aggregate cost and token metrics over a date range
    - Strictly filters by the authenticated user's org_id to prevent cross-tenant data leaks
    - Returns total cost, input/output/cached tokens, and request count
    
    Args:
        start_date: Start date for metrics range
        end_date: End date for metrics range
        org_context: Organization context from authentication dependency
        db: Database session
        
    Returns:
        MetricsSummaryResponse with aggregated metrics
    """
    # Query metrics filtered by org_id and date range
    # CRITICAL: org_id filter ensures tenant isolation
    result = db.query(
        func.sum(HourlyDailyUsageCache.raw_cost_usd).label("total_cost"),
        func.sum(HourlyDailyUsageCache.input_tokens).label("total_input"),
        func.sum(HourlyDailyUsageCache.output_tokens).label("total_output"),
        func.sum(HourlyDailyUsageCache.cached_tokens).label("total_cached"),
        func.count(HourlyDailyUsageCache.id).label("total_requests")
    ).filter(
        and_(
            HourlyDailyUsageCache.org_id == org_context.org_id,
            HourlyDailyUsageCache.timestamp_bucket >= start_date,
            HourlyDailyUsageCache.timestamp_bucket <= end_date
        )
    ).first()
    
    return MetricsSummaryResponse(
        total_cost_usd=float(result.total_cost or 0),
        total_input_tokens=int(result.total_input or 0),
        total_output_tokens=int(result.total_output or 0),
        total_cached_tokens=int(result.total_cached or 0),
        total_requests=int(result.total_requests or 0),
        start_date=start_date,
        end_date=end_date
    )


@router.get("/breakdown", response_model=MetricsBreakdownResponse)
async def get_metrics_breakdown(
    start_date: datetime,
    end_date: datetime,
    group_by: str,
    org_context: OrganizationContext = Depends(get_current_org),
    db: Session = Depends(get_db)
):
    """
    Get metrics grouped dynamically by model, provider, or api_key_id.
    
    This endpoint:
    - Groups metrics using the specified group_by parameter
    - Runs aggregations against the database with tenant's org_id filter
    - Prevents cross-tenant data leaks by strict org_id filtering
    
    Args:
        start_date: Start date for metrics range
        end_date: End date for metrics range
        group_by: Grouping dimension ('model', 'provider', or 'api_key_id')
        org_context: Organization context from authentication dependency
        db: Database session
        
    Returns:
        MetricsBreakdownResponse with grouped metrics
    """
    # Validate group_by parameter
    valid_group_by = ['model', 'provider', 'api_key_id']
    if group_by not in valid_group_by:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid group_by. Must be one of: {', '.join(valid_group_by)}"
        )
    
    # Map group_by to actual column
    group_column_map = {
        'model': HourlyDailyUsageCache.model,
        'provider': HourlyDailyUsageCache.provider,
        'api_key_id': HourlyDailyUsageCache.api_key_id
    }
    group_column = group_column_map[group_by]
    
    # Query grouped metrics filtered by org_id and date range
    # CRITICAL: org_id filter ensures tenant isolation
    query = db.query(
        group_column.label("group_key"),
        func.sum(HourlyDailyUsageCache.raw_cost_usd).label("total_cost"),
        func.sum(HourlyDailyUsageCache.input_tokens).label("input_tokens"),
        func.sum(HourlyDailyUsageCache.output_tokens).label("output_tokens"),
        func.sum(HourlyDailyUsageCache.cached_tokens).label("cached_tokens"),
        func.count(HourlyDailyUsageCache.id).label("request_count")
    ).filter(
        and_(
            HourlyDailyUsageCache.org_id == org_context.org_id,
            HourlyDailyUsageCache.timestamp_bucket >= start_date,
            HourlyDailyUsageCache.timestamp_bucket <= end_date
        )
    ).group_by(group_column)
    
    results = query.all()
    
    # Build breakdown items
    breakdown_items = [
        MetricsBreakdownItem(
            group_key=row.group_key,
            total_cost_usd=float(row.total_cost or 0),
            input_tokens=int(row.input_tokens or 0),
            output_tokens=int(row.output_tokens or 0),
            cached_tokens=int(row.cached_tokens or 0),
            request_count=int(row.request_count or 0)
        )
        for row in results
    ]
    
    return MetricsBreakdownResponse(
        breakdown=breakdown_items,
        start_date=start_date,
        end_date=end_date,
        group_by=group_by
    )


@router.get("/leak-detector", response_model=LeakDetectorResponse)
async def get_leak_detector_insights(
    org_context: OrganizationContext = Depends(get_current_org),
    db: Session = Depends(get_db)
):
    """
    Get automated cost-saving insights for the authenticated organization.
    
    This endpoint:
    - Surfaces insights like prompt cache-efficiency analysis and anomalies
    - Filters specifically for the logged-in organization's data
    - Provides actionable recommendations for cost optimization
    
    Args:
        org_context: Organization context from authentication dependency
        db: Database session
        
    Returns:
        LeakDetectorResponse with list of cost-saving insights
    """
    insights: List[LeakDetectorInsight] = []
    
    # CRITICAL: All queries filtered by org_id to prevent cross-tenant data leaks
    
    # Insight 1: Cache efficiency analysis
    cache_result = db.query(
        func.sum(HourlyDailyUsageCache.input_tokens).label("total_input"),
        func.sum(HourlyDailyUsageCache.cached_tokens).label("total_cached")
    ).filter(
        HourlyDailyUsageCache.org_id == org_context.org_id
    ).first()
    
    total_input = int(cache_result.total_input or 0)
    total_cached = int(cache_result.total_cached or 0)
    
    if total_input > 0:
        cache_efficiency = (total_cached / total_input) * 100
        if cache_efficiency < 10:
            insights.append(
                LeakDetectorInsight(
                    insight_type="cache_efficiency",
                    description=f"Low cache efficiency ({cache_efficiency:.1f}%). Consider optimizing prompts to increase cache hits.",
                    severity="medium",
                    potential_savings_usd=None,
                    metadata={"cache_efficiency_percent": cache_efficiency}
                )
            )
        elif cache_efficiency > 30:
            insights.append(
                LeakDetectorInsight(
                    insight_type="cache_efficiency",
                    description=f"Excellent cache efficiency ({cache_efficiency:.1f}%). Your prompt design is well-optimized.",
                    severity="low",
                    potential_savings_usd=None,
                    metadata={"cache_efficiency_percent": cache_efficiency}
                )
            )
    
    # Insight 2: Cost anomaly detection (compare recent vs previous period)
    recent_cost_result = db.query(
        func.sum(HourlyDailyUsageCache.raw_cost_usd).label("total_cost")
    ).filter(
        and_(
            HourlyDailyUsageCache.org_id == org_context.org_id,
            HourlyDailyUsageCache.timestamp_bucket >= datetime.utcnow() - func.interval('7 days')
        )
    ).first()
    
    recent_cost = float(recent_cost_result.total_cost or 0)
    
    if recent_cost > 1000:  # Threshold for high cost alert
        insights.append(
            LeakDetectorInsight(
                insight_type="cost_anomaly",
                description=f"High cost detected in the last 7 days: ${recent_cost:.2f}. Review usage patterns.",
                severity="high",
                potential_savings_usd=recent_cost * 0.1,  # Assume 10% potential savings
                metadata={"recent_7_day_cost_usd": recent_cost}
            )
        )
    
    # Insight 3: Provider cost comparison
    provider_costs = db.query(
        HourlyDailyUsageCache.provider,
        func.sum(HourlyDailyUsageCache.raw_cost_usd).label("total_cost")
    ).filter(
        and_(
            HourlyDailyUsageCache.org_id == org_context.org_id,
            HourlyDailyUsageCache.timestamp_bucket >= datetime.utcnow() - func.interval('30 days')
        )
    ).group_by(HourlyDailyUsageCache.provider).all()
    
    if len(provider_costs) > 1:
        # Find the most expensive provider
        most_expensive = max(provider_costs, key=lambda x: float(x.total_cost or 0))
        insights.append(
            LeakDetectorInsight(
                insight_type="provider_comparison",
                description=f"{most_expensive.provider} is your highest cost provider. Consider evaluating alternatives.",
                severity="low",
                potential_savings_usd=None,
                metadata={"provider_costs": {p.provider: float(p.total_cost or 0) for p in provider_costs}}
            )
        )
    
    return LeakDetectorResponse(
        insights=insights,
        total_insights=len(insights),
        generated_at=datetime.utcnow()
    )
