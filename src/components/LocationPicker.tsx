import React, { useState } from 'react';
import { MapPin, Navigation, X } from 'lucide-react';

interface LocationPickerProps {
  onLocationSelect: (location: { lat: number; lon: number; address: string }) => void;
  onClose: () => void;
}

export const LocationPicker: React.FC<LocationPickerProps> = ({ onLocationSelect, onClose }) => {
  const [manualLocation, setManualLocation] = useState({ lat: '', lon: '', address: '' });
  const [isGettingLocation, setIsGettingLocation] = useState(false);

  const handleCurrentLocation = () => {
    setIsGettingLocation(true);
    
    if (navigator.geolocation) {
      navigator.geolocation.getCurrentPosition(
        async (position) => {
          const { latitude, longitude } = position.coords;
          
          // Reverse geocoding to get address
          try {
            const response = await fetch(
              `https://api.opencagedata.com/geocode/v1/json?q=${latitude}+${longitude}&key=YOUR_API_KEY`
            );
            const data = await response.json();
            const address = data.results[0]?.formatted || `${latitude.toFixed(4)}, ${longitude.toFixed(4)}`;
            
            onLocationSelect({
              lat: latitude,
              lon: longitude,
              address: address
            });
          } catch (error) {
            onLocationSelect({
              lat: latitude,
              lon: longitude,
              address: `${latitude.toFixed(4)}, ${longitude.toFixed(4)}`
            });
          }
          
          setIsGettingLocation(false);
          onClose();
        },
        (error) => {
          console.error('Error getting location:', error);
          alert('Unable to get your location. Please enter manually.');
          setIsGettingLocation(false);
        }
      );
    } else {
      alert('Geolocation is not supported by this browser.');
      setIsGettingLocation(false);
    }
  };

  const handleManualSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    
    const lat = parseFloat(manualLocation.lat);
    const lon = parseFloat(manualLocation.lon);
    
    if (isNaN(lat) || isNaN(lon)) {
      alert('Please enter valid coordinates');
      return;
    }
    
    onLocationSelect({
      lat,
      lon,
      address: manualLocation.address || `${lat.toFixed(4)}, ${lon.toFixed(4)}`
    });
    
    onClose();
  };

  const predefinedLocations = [
    { name: 'Mumbai', lat: 19.0760, lon: 72.8777 },
    { name: 'Delhi', lat: 28.6139, lon: 77.2090 },
    { name: 'Chennai', lat: 13.0827, lon: 80.2707 },
    { name: 'Kolkata', lat: 22.5726, lon: 88.3639 },
    { name: 'Bangalore', lat: 12.9716, lon: 77.5946 },
    { name: 'Hyderabad', lat: 17.3850, lon: 78.4867 }
  ];

  return (
    <div className="absolute bottom-full mb-2 left-0 bg-white border border-gray-200 rounded-lg p-4 shadow-lg w-80">
      <div className="flex items-center justify-between mb-3">
        <h3 className="text-sm font-medium">Select Location</h3>
        <button onClick={onClose} className="text-gray-500 hover:text-gray-700">
          <X size={16} />
        </button>
      </div>

      {/* Current Location */}
      <button
        onClick={handleCurrentLocation}
        disabled={isGettingLocation}
        className="w-full flex items-center justify-center space-x-2 p-2 bg-blue-500 text-white rounded-lg hover:bg-blue-600 disabled:opacity-50 mb-3"
      >
        <Navigation size={16} />
        <span>{isGettingLocation ? 'Getting location...' : 'Use Current Location'}</span>
      </button>

      {/* Predefined Locations */}
      <div className="mb-3">
        <div className="text-xs text-gray-600 mb-2">Quick Select:</div>
        <div className="grid grid-cols-2 gap-1">
          {predefinedLocations.map((location) => (
            <button
              key={location.name}
              onClick={() => {
                onLocationSelect({
                  lat: location.lat,
                  lon: location.lon,
                  address: location.name
                });
                onClose();
              }}
              className="p-1 text-xs bg-gray-100 hover:bg-gray-200 rounded"
            >
              {location.name}
            </button>
          ))}
        </div>
      </div>

      {/* Manual Entry */}
      <form onSubmit={handleManualSubmit} className="space-y-2">
        <div className="text-xs text-gray-600">Manual Entry:</div>
        <div className="grid grid-cols-2 gap-2">
          <input
            type="number"
            step="any"
            placeholder="Latitude"
            value={manualLocation.lat}
            onChange={(e) => setManualLocation(prev => ({ ...prev, lat: e.target.value }))}
            className="px-2 py-1 text-xs border border-gray-300 rounded"
          />
          <input
            type="number"
            step="any"
            placeholder="Longitude"
            value={manualLocation.lon}
            onChange={(e) => setManualLocation(prev => ({ ...prev, lon: e.target.value }))}
            className="px-2 py-1 text-xs border border-gray-300 rounded"
          />
        </div>
        <input
          type="text"
          placeholder="Address (optional)"
          value={manualLocation.address}
          onChange={(e) => setManualLocation(prev => ({ ...prev, address: e.target.value }))}
          className="w-full px-2 py-1 text-xs border border-gray-300 rounded"
        />
        <button
          type="submit"
          className="w-full p-1 text-xs bg-green-500 text-white rounded hover:bg-green-600"
        >
          Set Location
        </button>
      </form>
    </div>
  );
};