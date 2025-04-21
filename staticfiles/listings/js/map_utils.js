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
        attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors',
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

    console.log("query", query);
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

    const mergedOptions = {...defaultOptions, ...options };

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
            console.log("response", response);
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
            console.log("error", error);
            console.log("error.message", error.message);
            console.log("error.name", error.name);
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

    const mergedOptions = {...defaultOptions, ...options };

    fetch(
            `https://nominatim.openstreetmap.org/reverse?format=json&lat=${lat}&lon=${lng}`, {
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

function initializeLocationName() {
    // Initialize location name if coordinates exist
    const searchLat = document.getElementById("search-lat").value;
    const searchLng = document.getElementById("search-lng").value;

    if (searchLat && searchLng && searchLat !== "None" && searchLng !== "None") {
        console.log("searchLat", searchLat);
        console.log("searchLng", searchLng);

        // Ensure we have valid numbers
        const lat = parseFloat(searchLat);
        const lng = parseFloat(searchLng);

        if (!isNaN(lat) && !isNaN(lng)) {
            const latlng = L.latLng(lat, lng);

            // Place marker and center map
            placeMarker(latlng);
            searchMap.setView(latlng, 15);

            // Get location name for the coordinates
            reverseGeocode(lat, lng, {
                onSuccess: (result) => {
                    // Update the search input with the location name
                    document.getElementById("location-search").value = result.displayName;
                    // Expand the filter panel by removing the collapsed class and ensuring content is visible
                    const filterPanel = document.getElementById("filter-panel");
                    if (filterPanel) {
                        // This might be more reliable as it would use the existing toggle logic
                        const toggleButton = document.getElementById("toggle-filters");
                        if (toggleButton && filterPanel.classList.contains("collapsed")) {
                            toggleButton.click();
                        }
                    }
                    // Make sure the marker has a popup with the location name
                    if (searchMarker) {
                        searchMarker.bindPopup(result.displayName).openPopup();

                        // Also set a default popup in case reverse geocoding fails
                        searchMarker.setPopupContent(result.displayName);
                    }
                },
                onError: () => {
                    // If reverse geocoding fails, still show a popup with coordinates
                    if (searchMarker) {
                        const fallbackContent = `Location at ${lat.toFixed(
                            6
                        )}, ${lng.toFixed(6)}`;
                        searchMarker.bindPopup(fallbackContent).openPopup();
                    }
                },
            });

            // Fix map rendering
            setTimeout(() => {
                searchMap.invalidateSize();

                // Make sure marker is visible after map is properly rendered
                if (searchMarker) {
                    searchMarker.openPopup();
                }
            }, 100);
        }
    }
}

function addListingsToMap() {
    console.log("Starting addListingsToMap...");
    // TODO: change so that the listings are not depended on the html structure
    // Add markers for all listings (as in original code)
    const listings = document.querySelectorAll(".card");
    console.log("Found listings:", listings.length);
    const bounds = [];

    // Ensure listingLayerGroup exists
    if (!listingLayerGroup) {
        console.log("Creating new listingLayerGroup");
        listingLayerGroup = L.layerGroup().addTo(searchMap);
    } else {
        console.log("Clearing existing listingLayerGroup");
        // Clear existing markers
        listingLayerGroup.clearLayers();
    }

    listings.forEach((listing) => {
        try {
            console.log("Processing listing:", listing);
            const location = parseLocation(listing.dataset.location);
            console.log("Parsed location:", location);
            const locationName = listing.dataset.locationName;
            const title = listing.dataset.title;
            const price = listing.dataset.price;
            const rating = parseFloat(listing.dataset.rating) || 0;

            console.log(
                `Adding listing: ${title} at ${location.lat}, ${location.lng}`
            );

            // Create the marker but add it to the layer group instead of the map
            const marker = L.marker([location.lat, location.lng], {
                zIndexOffset: 1000, // Higher z-index to appear above garage markers
            });

            listingLayerGroup.addLayer(marker);
            bounds.push([location.lat, location.lng]);

            // Create popup content
            const ratingHtml = rating ?
                `<div style="margin-bottom: 8px; display: flex; align-items: center;">
                    <i class="fas fa-star" style="color: #f1c40f; margin-right: 8px;"></i>
                    <span style="color: #34495e; font-size: 13px;">${rating.toFixed(1)} (${generateStarRating(rating)})</span>
                </div>` :
                `<div style="margin-bottom: 8px; display: flex; align-items: center;">
                    <i class="fas fa-star" style="color: #bdc3c7; margin-right: 8px;"></i>
                    <span style="color: #7f8c8d; font-size: 13px;">No reviews yet</span>
                </div>`;

            const popupContent = `
                <div class="listing-popup" style="padding: 8px; min-width: 200px;">
                    <div style="margin-bottom: 12px;">
                        <h4 style="margin: 0; color: #2c3e50; font-size: 16px;">${title}</h4>
                    </div>
                    <div style="margin-bottom: 10px; display: flex; align-items: flex-start;">
                        <i class="fas fa-map-marker-alt" style="color: #7f8c8d; margin-right: 8px; margin-top: 3px;"></i>
                        <div style="color: #34495e; font-size: 13px;">${locationName}</div>
                    </div>
                    <div style="margin-bottom: 8px; display: flex; align-items: center;">
                        <i class="fas fa-tag" style="color: #7f8c8d; margin-right: 8px;"></i>
                        <span style="color: #34495e; font-size: 13px;">$${Math.abs(price).toFixed(2)}/hour</span>
                    </div>
                    ${ratingHtml}
                </div>
            `;

            marker.bindPopup(popupContent);
            console.log("Successfully added marker for listing:", title);
        } catch (error) {
            console.error("Error adding listing marker:", error);
        }
    });

    // Fit map to bounds if we have any markers
    if (bounds.length > 0) {
        console.log("Fitting map to bounds");
        searchMap.fitBounds(bounds);
    } else {
        console.log("No bounds to fit to");
    }
}

// Create a new map legend with toggle functionality
function createMapLegend() {
    const legend = L.control({ position: 'bottomright' });

    legend.onAdd = function(map) {
        const div = L.DomUtil.create('div', 'map-legend');
        div.innerHTML = `
            <div style="background: white; padding: 8px; border-radius: 4px; box-shadow: 0 1px 5px rgba(0,0,0,0.4); font-size: 12px;">
                <div style="font-weight: bold; margin-bottom: 5px; text-align: center;">Map Legend</div>
                
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

        // Add event listener to the listings toggle switch
        setTimeout(() => {
            const toggleListings = document.getElementById('toggle-listings');

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