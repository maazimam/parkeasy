// NYC map bounds and configuration
const NYC_BOUNDS = {
  min_lat: 40.477399, // Southernmost point of NYC
  max_lat: 40.917577, // Northernmost point of NYC
  min_lng: -74.25909, // Westernmost point of NYC
  max_lng: -73.700272, // Easternmost point of NYC
};

// Create a Leaflet bounds object from the NYC bounds
const NYC_LEAFLET_BOUNDS = [
  [NYC_BOUNDS.min_lat, NYC_BOUNDS.min_lng], // Southwest corner
  [NYC_BOUNDS.max_lat, NYC_BOUNDS.max_lng], // Northeast corner
];

// NYC center coordinates (approximate)
const NYC_CENTER = [40.7128, -74.006];

// Function to initialize a map with NYC bounds
function initializeNYCMap(mapElementId, options = {}) {
  // Create the map with NYC center
  const map = L.map(mapElementId, {
    center: options.center || NYC_CENTER,
    zoom: options.zoom || 11,
    maxBounds: NYC_LEAFLET_BOUNDS,
    minZoom: options.minZoom || 10,
    ...options,
  });

  // Add the tile layer
  L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png", {
    attribution:
      '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors',
  }).addTo(map);

  // Set max bounds with padding to prevent scrolling too far outside NYC
  map.setMaxBounds(map.getBounds().pad(0.1));

  return map;
}

// Nominatim API utilities

/**
 * Check if coordinates are within NYC bounds
 * @param {number} lat - Latitude
 * @param {number} lng - Longitude
 * @returns {boolean} - True if coordinates are within NYC bounds
 */
function isWithinNYC(lat, lng) {
  return (
    lat >= NYC_BOUNDS.min_lat &&
    lat <= NYC_BOUNDS.max_lat &&
    lng >= NYC_BOUNDS.min_lng &&
    lng <= NYC_BOUNDS.max_lng
  );
}

/**
 * Search for a location using Nominatim
 * @param {string} query - Search query
 * @param {Object} options - Options for the search
 * @param {boolean} options.restrictToNYC - Whether to restrict results to NYC
 * @param {Function} options.onSuccess - Callback for successful search
 * @param {Function} options.onOutOfBounds - Callback for when result is out of NYC bounds
 * @param {Function} options.onNotFound - Callback for when no results are found
 * @param {Function} options.onError - Callback for errors
 */
function searchLocation(query, options = {}) {
  if (!query) {
    if (options.onError) options.onError("No search query provided");
    return;
  }

  const defaultOptions = {
    restrictToNYC: true,
    onSuccess: () => {},
    onOutOfBounds: () =>
      alert(
        "Location is outside of New York City. Please search for a location within NYC."
      ),
    onNotFound: () =>
      alert("Location not found. Please try a different search term."),
    onError: (error) => {
      console.error("Search error:", error);
      alert("Error searching for location. Please try again.");
    },
  };

  const mergedOptions = { ...defaultOptions, ...options };

  // Build the URL
  let url = `https://nominatim.openstreetmap.org/search?format=json&q=${encodeURIComponent(
    query
  )}`;

  // Add viewbox parameter if restricting to NYC
  if (mergedOptions.restrictToNYC) {
    url += `&viewbox=${NYC_BOUNDS.min_lng},${NYC_BOUNDS.min_lat},${NYC_BOUNDS.max_lng},${NYC_BOUNDS.max_lat}&bounded=1`;
  }

  // Add CORS headers to the request
  fetch(url, {
    headers: {
      Accept: "application/json",
      "User-Agent": "ParkEasy NYC Application (https://parkeasy.example.com)",
    },
    mode: "cors", // Try with explicit CORS mode
  })
    .then((response) => {
      if (!response.ok) {
        throw new Error(`HTTP error! Status: ${response.status}`);
      }
      return response.json();
    })
    .then((data) => {
      if (data && data.length > 0) {
        const location = data[0];
        const lat = parseFloat(location.lat);
        const lng = parseFloat(location.lon);

        // Check if within NYC bounds if restriction is enabled
        if (!mergedOptions.restrictToNYC || isWithinNYC(lat, lng)) {
          mergedOptions.onSuccess({
            lat,
            lng,
            displayName: location.display_name,
            raw: location,
          });
        } else {
          mergedOptions.onOutOfBounds();
        }
      } else {
        mergedOptions.onNotFound();
      }
    })
    .catch((error) => {
      console.error("Nominatim API error:", error);

      // Fallback for CORS issues - use a hardcoded NYC location
      if (error.message.includes("CORS") || error.name === "TypeError") {
        console.warn("CORS issue detected, using fallback NYC location");

        // Use a fallback location in NYC (Times Square)
        const fallbackLocation = {
          lat: 40.758,
          lng: -73.9855,
          displayName: "Times Square, Manhattan, NYC",
        };

        alert(
          "Location search is currently unavailable. Using a default NYC location."
        );
        mergedOptions.onSuccess(fallbackLocation);
      } else {
        mergedOptions.onError(error);
      }
    });
}

/**
 * Reverse geocode coordinates to get address
 * @param {number} lat - Latitude
 * @param {number} lng - Longitude
 * @param {Object} options - Options for the reverse geocoding
 * @param {Function} options.onSuccess - Callback for successful reverse geocoding
 * @param {Function} options.onError - Callback for errors
 */
function reverseGeocode(lat, lng, options = {}) {
  const defaultOptions = {
    onSuccess: () => {},
    onError: (error) => {
      console.error("Reverse geocoding error:", error);
    },
  };

  const mergedOptions = { ...defaultOptions, ...options };

  fetch(
    `https://nominatim.openstreetmap.org/reverse?format=json&lat=${lat}&lon=${lng}`,
    {
      headers: {
        Accept: "application/json",
        "User-Agent": "ParkEasy NYC Application (https://parkeasy.example.com)",
      },
      mode: "cors", // Try with explicit CORS mode
    }
  )
    .then((response) => {
      if (!response.ok) {
        throw new Error(`HTTP error! Status: ${response.status}`);
      }
      return response.json();
    })
    .then((data) => {
      if (data && data.display_name) {
        mergedOptions.onSuccess({
          displayName: data.display_name,
          raw: data,
        });
      } else {
        mergedOptions.onError("No address found for these coordinates");
      }
    })
    .catch((error) => {
      console.error("Nominatim API error:", error);

      // Fallback for CORS issues - generate a simple address
      if (error.message.includes("CORS") || error.name === "TypeError") {
        console.warn("CORS issue detected, using fallback address generation");

        // Create a simple address string using the coordinates
        const simplifiedAddress = `Location at ${lat.toFixed(4)}, ${lng.toFixed(
          4
        )}`;

        mergedOptions.onSuccess({
          displayName: simplifiedAddress,
          raw: { display_name: simplifiedAddress },
        });
      } else {
        mergedOptions.onError(error);
      }
    });
}


// Create a new map legend with toggle functionality
function createMapLegend() {
  const legend = L.control({ position: 'bottomright' });

  legend.onAdd = function(map) {
      const div = L.DomUtil.create('div', 'map-legend');
      div.innerHTML = `
          <div style="background: white; padding: 8px; border-radius: 4px; box-shadow: 0 1px 5px rgba(0,0,0,0.4); font-size: 12px;">
              <div style="font-weight: bold; margin-bottom: 5px; text-align: center;">Map Legend</div>
              
              <div style="display: flex; align-items: center; margin-bottom: 5px;">
                  <input type="checkbox" id="toggle-garages" checked style="margin-right: 5px;">
                  <div style="
                      background-color: #2c3e50; 
                      width: 20px; 
                      height: 20px; 
                      border-radius: 5px;
                      display: flex; 
                      justify-content: center; 
                      align-items: center; 
                      border: 2px solid white; 
                      box-shadow: 0 1px 3px rgba(0,0,0,0.4);
                      margin-right: 8px;
                      margin-left: 3px;
                  ">
                      <i class="fas fa-car" style="color: white; font-size: 10px; transform: rotate(-45deg);"></i>
                  </div>
                  <label for="toggle-garages">Parking Garages</label>
              </div>
              
              <div style="display: flex; align-items: center;">
                  <input type="checkbox" id="toggle-listings" checked style="margin-right: 5px;">
                  <div style="
                      background-color: #3388ff; 
                      width: 20px; 
                      height: 20px; 
                      border-radius: 50%;
                      border: 2px solid white; 
                      box-shadow: 0 1px 3px rgba(0,0,0,0.4);
                      margin-right: 8px;
                      margin-left: 3px;
                  "></div>
                  <label for="toggle-listings">Available Listings</label>
              </div>
          </div>
      `;
      
      // Prevent clicks on the legend from propagating to the map
      L.DomEvent.disableClickPropagation(div);
      
      // Add event listeners to the toggle switches after a slight delay to ensure DOM is ready
      setTimeout(() => {
          const toggleGarages = document.getElementById('toggle-garages');
          const toggleListings = document.getElementById('toggle-listings');
          
          if (toggleGarages) {
              toggleGarages.addEventListener('change', function() {
                  if (this.checked) {
                      if (!map.hasLayer(garageLayerGroup)) {
                          map.addLayer(garageLayerGroup);
                      }
                  } else {
                      if (map.hasLayer(garageLayerGroup)) {
                          map.removeLayer(garageLayerGroup);
                      }
                  }
              });
          }
          
          if (toggleListings) {
              toggleListings.addEventListener('change', function() {
                  if (this.checked) {
                      if (!map.hasLayer(listingLayerGroup)) {
                          map.addLayer(listingLayerGroup);
                      }
                  } else {
                      if (map.hasLayer(listingLayerGroup)) {
                          map.removeLayer(listingLayerGroup);
                      }
                  }
              });
          }
      }, 100);
      
      return div;
  };

  return legend;
}

// This is a simpler function that directly adds garages to the map
function addGaragesDirectly(map) {
  console.log("Adding garages directly to map...");
  currentMap = map;
  
  // Create layer group if it doesn't exist
  if (!garageLayerGroup) {
      garageLayerGroup = L.layerGroup().addTo(map);
  }

  // Create marker icon - code remains the same
  const garageIcon = L.divIcon({
      html: `<div style="
          background-color: #2c3e50; 
          width: 22px;   /* Reduced from 28px */
          height: 22px;  /* Reduced from 28px */
          border-radius: 5px;
          display: flex; 
          justify-content: center; 
          align-items: center; 
          border: 1px solid white; /* Thinner border */
          box-shadow: 0 1px 3px rgba(0,0,0,0.4);
      ">
          <i class="fas fa-car" style="
              color: white; 
              font-size: 11px;  /* Reduced from 14px */
              transform: rotate(-45deg);
          "></i>
      </div>`,
      className: 'garage-marker',
      iconSize: [22, 22],     /* Reduced from [28, 28] */
      iconAnchor: [11, 22],   /* Adjusted for new size */
      popupAnchor: [0, -22]   /* Adjusted for new size */
  });

  // Create backup markers to use if API fails
  const backupGarages = [
      {
          name: "SUTTON 53 PARKING LLC",
          address: "410 EAST 54 STREET, NEW YORK, NY 10022",
          phone: "(877) 727-5464",
          lat: 40.757700,
          lng: -73.963900
      },
      {
          name: "TIMES SQUARE GARAGE", 
          address: "224 WEST 49TH STREET, NEW YORK, NY 10019",
          phone: "(212) 333-7275",
          lat: 40.760800,
          lng: -73.984700
      }
  ];

  if (!map) {
      console.error("Map object is null or undefined in addGaragesDirectly!");
      return;
  }

  // Add each garage marker from backup if needed
  function addBackupMarkers() {
      backupGarages.forEach((garage, index) => {
          try {
              console.log(`Adding backup garage ${index+1}/${backupGarages.length}: "${garage.name}" at ${garage.lat}, ${garage.lng}`);

              // Create marker and add to LAYER GROUP instead of map
              const marker = L.marker([garage.lat, garage.lng], {
                  icon: garageIcon,
                  title: garage.name,
                  zIndexOffset: 100  // Lower z-index to ensure garages stay behind listings
              });
              
              garageLayerGroup.addLayer(marker);

              // Create popup content
              const popupContent = `
                  <div class="garage-popup">
                      <h4 class="garage-name">${garage.name}</h4>
                      <div class="garage-address">
                          <i class="fas fa-map-marker-alt"></i>
                          <div>${garage.address}</div>
                      </div>
                      <div class="garage-phone">
                          <i class="fas fa-phone"></i>
                          <a href="tel:${garage.phone}">${garage.phone}</a>
                      </div>
                  </div>
              `;

              // Bind popup to marker
              marker.bindPopup(popupContent);
              
              // Open popup for first marker
              if (index === 0) {
                  setTimeout(() => {
                      marker.openPopup();
                  }, 500);
              }
          } catch (error) {
              console.error(`Error adding backup garage ${garage.name}:`, error);
          }
      });
  }

  // Try to fetch garages from NYC Open Data API
  fetch('https://data.cityofnewyork.us/resource/5bhr-pjxt.json?$limit=50')
      .then(response => {
          if (!response.ok) {
              throw new Error('Network response was not ok');
          }
          return response.json();
      })
      .then(garages => {
          console.log(`Fetched ${garages.length} garages from NYC API`);
          
          // Add markers for each garage
          garages.forEach(garage => {
              // Only add markers if we have coordinates
              if (garage.latitude && garage.longitude) {
                  try {
                      const lat = parseFloat(garage.latitude);
                      const lng = parseFloat(garage.longitude);
                      
                      // Format the address string
                      const address = [
                          garage.address_building, 
                          garage.address_street_name,
                          garage.address_city, 
                          garage.address_state,
                          garage.address_zip
                      ].filter(Boolean).join(' ');
                      
                      // Get capacity info
                      let capacity = "";
                      if (garage.detail) {
                          capacity = garage.detail;
                      }
                      
                      // Create marker and add to LAYER GROUP instead of map
                      const marker = L.marker([lat, lng], {
                          icon: garageIcon,
                          title: garage.business_name,
                          zIndexOffset: 100  // Lower z-index to ensure garages stay behind listings
                      });
                      
                      garageLayerGroup.addLayer(marker);
                      
                      // Create popup content
                      const popupContent = `
                          <div class="garage-popup">
                              <h4 class="garage-name">${garage.business_name}</h4>
                              <div class="garage-address">
                                  <i class="fas fa-map-marker-alt"></i>
                                  <div>${address}</div>
                              </div>
                              ${garage.contact_phone ? `
                              <div class="garage-phone">
                                  <i class="fas fa-phone"></i>
                                  <a href="tel:${garage.contact_phone}">${garage.contact_phone}</a>
                              </div>` : ''}
                              ${capacity ? `
                              <div class="garage-details">
                                  <i class="fas fa-info-circle"></i>
                                  <div>${capacity}</div>
                              </div>` : ''}
                          </div>
                      `;
                      
                      // Bind popup to marker
                      marker.bindPopup(popupContent);
                      
                  } catch (error) {
                      console.error(`Error adding garage ${garage.business_name}:`, error);
                  }
              }
          });
          
          // Center map on NYC after adding garages
          map.setView([40.7128, -74.0060], 12);
      })
      .catch(error => {
          console.error('Error fetching garage data:', error);
          
          // If API fails, add default markers as fallback
          console.log("API fetch failed, adding backup garage markers");
          addBackupMarkers();
      });

  console.log("Garage data request initiated");
}
