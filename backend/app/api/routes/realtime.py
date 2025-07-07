from fastapi import APIRouter, HTTPException, Query
from typing import Optional, Dict, Any
import logging
import asyncio
import aiohttp
from datetime import datetime, timedelta
import json

logger = logging.getLogger(__name__)

router = APIRouter()

class RealTimeDataService:
    """Service for fetching real-time data from MOSDAC and other sources"""
    
    def __init__(self):
        self.mosdac_base_url = "https://www.mosdac.gov.in"
        self.session = None
    
    async def get_session(self):
        if not self.session:
            self.session = aiohttp.ClientSession()
        return self.session
    
    async def close_session(self):
        if self.session:
            await self.session.close()
            self.session = None

# Global service instance
realtime_service = RealTimeDataService()

@router.get("/weather/realtime")
async def get_realtime_weather(
    lat: Optional[float] = Query(None, description="Latitude"),
    lon: Optional[float] = Query(None, description="Longitude"),
    location: Optional[str] = Query(None, description="Location name")
):
    """Get real-time weather data"""
    try:
        # Mock real-time weather data (replace with actual MOSDAC API calls)
        weather_data = {
            "location": {
                "lat": lat or 19.0760,
                "lon": lon or 72.8777,
                "name": location or "Mumbai"
            },
            "current": {
                "temperature": 28.5,
                "humidity": 78,
                "pressure": 1013.2,
                "wind_speed": 12.5,
                "wind_direction": 225,
                "visibility": 8.0,
                "cloud_cover": 65,
                "uv_index": 6
            },
            "forecast": [
                {
                    "time": (datetime.now() + timedelta(hours=i)).isoformat(),
                    "temperature": 28.5 + (i * 0.5),
                    "humidity": 78 - (i * 2),
                    "precipitation_probability": min(30 + (i * 5), 80)
                }
                for i in range(24)
            ],
            "satellite_data": {
                "source": "INSAT-3D",
                "last_updated": datetime.now().isoformat(),
                "cloud_motion_vectors": True,
                "precipitation_estimate": 2.5
            },
            "alerts": [
                {
                    "type": "thunderstorm",
                    "severity": "moderate",
                    "message": "Thunderstorms possible in the evening",
                    "valid_until": (datetime.now() + timedelta(hours=6)).isoformat()
                }
            ]
        }
        
        return {
            "status": "success",
            "data": weather_data,
            "timestamp": datetime.now().isoformat(),
            "source": "MOSDAC Real-time API"
        }
        
    except Exception as e:
        logger.error(f"Error fetching real-time weather data: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Error fetching weather data: {str(e)}"
        )

@router.get("/ocean/realtime")
async def get_realtime_ocean(
    lat: Optional[float] = Query(None, description="Latitude"),
    lon: Optional[float] = Query(None, description="Longitude"),
    region: Optional[str] = Query(None, description="Ocean region")
):
    """Get real-time ocean data"""
    try:
        # Mock real-time ocean data
        ocean_data = {
            "location": {
                "lat": lat or 15.0,
                "lon": lon or 70.0,
                "region": region or "Arabian Sea"
            },
            "current": {
                "sea_surface_temperature": 29.2,
                "wave_height": 1.8,
                "wave_period": 8.5,
                "wave_direction": 270,
                "current_speed": 0.45,
                "current_direction": 180,
                "salinity": 35.2,
                "chlorophyll_concentration": 0.8
            },
            "satellite_data": {
                "source": "OCEANSAT-2",
                "last_updated": datetime.now().isoformat(),
                "sst_quality": "high",
                "chlorophyll_quality": "medium"
            },
            "buoy_data": {
                "nearest_buoy": "BD11",
                "distance_km": 45.2,
                "last_report": (datetime.now() - timedelta(minutes=30)).isoformat()
            },
            "forecast": [
                {
                    "time": (datetime.now() + timedelta(hours=i*6)).isoformat(),
                    "wave_height": 1.8 + (i * 0.1),
                    "sst": 29.2 - (i * 0.05)
                }
                for i in range(8)
            ]
        }
        
        return {
            "status": "success",
            "data": ocean_data,
            "timestamp": datetime.now().isoformat(),
            "source": "MOSDAC Ocean Data Service"
        }
        
    except Exception as e:
        logger.error(f"Error fetching real-time ocean data: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Error fetching ocean data: {str(e)}"
        )

@router.get("/satellites/status")
async def get_satellite_status():
    """Get current satellite status and data availability"""
    try:
        # Mock satellite status data
        satellites = [
            {
                "name": "INSAT-3D",
                "status": "operational",
                "last_contact": datetime.now().isoformat(),
                "orbit_position": "82°E",
                "instruments": {
                    "imager": {"status": "active", "last_image": datetime.now().isoformat()},
                    "sounder": {"status": "active", "last_data": datetime.now().isoformat()}
                },
                "data_products": ["weather", "cloud_motion", "temperature_profile"],
                "coverage": "Indian subcontinent"
            },
            {
                "name": "SCATSAT-1",
                "status": "operational",
                "last_contact": (datetime.now() - timedelta(minutes=45)).isoformat(),
                "orbit_type": "polar",
                "instruments": {
                    "scatterometer": {"status": "active", "last_data": datetime.now().isoformat()}
                },
                "data_products": ["ocean_winds", "soil_moisture"],
                "coverage": "global"
            },
            {
                "name": "OCEANSAT-2",
                "status": "operational",
                "last_contact": (datetime.now() - timedelta(minutes=20)).isoformat(),
                "orbit_type": "polar",
                "instruments": {
                    "ocm": {"status": "active", "last_data": datetime.now().isoformat()},
                    "scatterometer": {"status": "active", "last_data": datetime.now().isoformat()}
                },
                "data_products": ["ocean_color", "sst", "ocean_winds"],
                "coverage": "global oceans"
            }
        ]
        
        return {
            "status": "success",
            "satellites": satellites,
            "total_active": len([s for s in satellites if s["status"] == "operational"]),
            "last_updated": datetime.now().isoformat(),
            "data_latency": {
                "weather": "15 minutes",
                "ocean": "30 minutes",
                "winds": "45 minutes"
            }
        }
        
    except Exception as e:
        logger.error(f"Error fetching satellite status: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Error fetching satellite status: {str(e)}"
        )

@router.get("/cyclone/tracking")
async def get_cyclone_tracking():
    """Get current cyclone tracking data"""
    try:
        # Mock cyclone data
        cyclones = [
            {
                "id": "CYC_2024_001",
                "name": "CYCLONE_BIPARJOY",
                "status": "active",
                "category": "Category 2",
                "current_position": {
                    "lat": 20.5,
                    "lon": 68.2,
                    "timestamp": datetime.now().isoformat()
                },
                "intensity": {
                    "max_wind_speed": 95,
                    "central_pressure": 980,
                    "movement_speed": 12,
                    "movement_direction": 45
                },
                "forecast_track": [
                    {
                        "time": (datetime.now() + timedelta(hours=i*6)).isoformat(),
                        "lat": 20.5 + (i * 0.2),
                        "lon": 68.2 + (i * 0.3),
                        "intensity": max(50, 95 - (i * 5))
                    }
                    for i in range(12)
                ],
                "affected_areas": ["Gujarat coast", "Rajasthan", "Southern Pakistan"],
                "warnings": [
                    {
                        "type": "storm_surge",
                        "level": "high",
                        "areas": ["Kutch", "Saurashtra"]
                    }
                ]
            }
        ]
        
        return {
            "status": "success",
            "active_cyclones": cyclones,
            "total_active": len(cyclones),
            "last_updated": datetime.now().isoformat(),
            "data_source": "IMD Cyclone Warning Division"
        }
        
    except Exception as e:
        logger.error(f"Error fetching cyclone data: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Error fetching cyclone data: {str(e)}"
        )

@router.get("/alerts")
async def get_weather_alerts(
    region: Optional[str] = Query(None, description="Region filter")
):
    """Get current weather alerts and warnings"""
    try:
        alerts = [
            {
                "id": "ALERT_001",
                "type": "thunderstorm",
                "severity": "moderate",
                "region": "Mumbai Metropolitan Region",
                "message": "Thunderstorms with lightning expected between 3 PM to 8 PM",
                "issued_at": datetime.now().isoformat(),
                "valid_until": (datetime.now() + timedelta(hours=5)).isoformat(),
                "source": "IMD Mumbai"
            },
            {
                "id": "ALERT_002",
                "type": "heavy_rainfall",
                "severity": "high",
                "region": "Kerala",
                "message": "Heavy to very heavy rainfall expected in next 24 hours",
                "issued_at": (datetime.now() - timedelta(hours=2)).isoformat(),
                "valid_until": (datetime.now() + timedelta(hours=22)).isoformat(),
                "source": "IMD Thiruvananthapuram"
            }
        ]
        
        if region:
            alerts = [a for a in alerts if region.lower() in a["region"].lower()]
        
        return {
            "status": "success",
            "alerts": alerts,
            "total_alerts": len(alerts),
            "last_updated": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error fetching weather alerts: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Error fetching alerts: {str(e)}"
        )

# Cleanup on shutdown
@router.on_event("shutdown")
async def shutdown_event():
    await realtime_service.close_session()