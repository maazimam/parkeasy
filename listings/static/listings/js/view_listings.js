// Modified view_listings.js for three-pane layout
console.log("Modified view_listings.js loaded");

// Helper function to generate star HTML - extract it so it can be used anywhere
function generateStarRating(rating) {
  let starsHtml = "";

  if (!rating) {
    // Show 5 empty stars if no rating
    for (let i = 0; i < 5; i++) {
      starsHtml += '<i class="far fa-star text-warning"></i>';
    }
  } else {
    // Full stars
    for (let i = 0; i < Math.floor(rating); i++) {
      starsHtml += '<i class="fas fa-star text-warning"></i>';
    }
    // Half star
    if (rating % 1 >= 0.5) {
      starsHtml += '<i class="fas fa-star-half-alt text-warning"></i>';
    }
    // Empty stars
    for (let i = Math.ceil(rating); i < 5; i++) {
      starsHtml += '<i class="far fa-star text-warning"></i>';
    }
  }

  return starsHtml;
}

// Global variables
let searchMap;
let searchMarker;
let mapInitialized = false;
let listingMarkers = []; // Keep track of all listing markers

// Map-related functions (outside DOMContentLoaded)
function initializeMap() {
  if (!mapInitialized) {
    // Always initialize the map in the map-view panel
    searchMap = initializeNYCMap("map-view");

    // Add click event to map
    searchMap.on("click", onMapClick);
    mapInitialized = true;

    // Add all listing markers immediately
    addListingMarkersToMap();
  }
}

function onMapClick(e) {
  // Only update if we're in search mode (not viewing listings)
  placeMarker(e.latlng);
  updateCoordinates(e.latlng.lat, e.latlng.lng);

  // Reverse geocode to get location name
  reverseGeocode(e.latlng.lat, e.latlng.lng, {
    onSuccess: (result) => {
      document.getElementById("location-search").value = result.displayName;
    },
  });
}

function placeMarker(latlng) {
  if (searchMarker) {
    searchMap.removeLayer(searchMarker);
  }

  // Create a special search marker that stands out from listing markers
  searchMarker = L.marker(latlng, {
    draggable: true,
    icon: L.divIcon({
      className: "search-marker-icon",
      html: '<div style="background-color: #ff3b30; width: 20px; height: 20px; border-radius: 50%; border: 2px solid white;"></div>',
      iconSize: [20, 20],
      iconAnchor: [10, 10],
    }),
  }).addTo(searchMap);

  // Update coordinates when marker is dragged
  searchMarker.on("dragend", function (event) {
    const marker = event.target;
    const position = marker.getLatLng();
    updateCoordinates(position.lat, position.lng);

    // Reverse geocode to get location name
    reverseGeocode(position.lat, position.lng, {
      onSuccess: (result) => {
        document.getElementById("location-search").value = result.displayName;
        marker.bindPopup(result.displayName);
      },
    });

    // Draw search radius if enabled
    drawSearchRadius(position);
  });

  // Draw search radius if enabled
  drawSearchRadius(latlng);
}

// Add search radius visualization
let radiusCircle = null;
function drawSearchRadius(center) {
  // Remove existing radius circle if it exists
  if (radiusCircle) {
    searchMap.removeLayer(radiusCircle);
    radiusCircle = null;
  }

  // Check if radius filtering is enabled
  const enableRadiusCheckbox = document.getElementById("enable-radius");
  const radiusInput = document.getElementById("radius-input");

  if (
    enableRadiusCheckbox &&
    enableRadiusCheckbox.checked &&
    radiusInput &&
    radiusInput.value
  ) {
    const radiusKm = parseFloat(radiusInput.value);
    if (!isNaN(radiusKm) && radiusKm > 0) {
      // Convert km to meters for the circle radius
      const radiusMeters = radiusKm * 1000;

      // Create a circle with styling
      radiusCircle = L.circle(center, {
        radius: radiusMeters,
        color: "#007bff",
        fillColor: "#007bff",
        fillOpacity: 0.1,
        weight: 2,
        dashArray: "5, 5",
      }).addTo(searchMap);

      // Fit map to show the entire circle
      searchMap.fitBounds(radiusCircle.getBounds());
    }
  }
}

function updateCoordinates(lat, lng) {
  document.getElementById("search-lat").value = lat;
  document.getElementById("search-lng").value = lng;

  // Update coordinate display
  const coordDisplay = document.getElementById("coordinates-display");
  if (coordDisplay) {
    coordDisplay.style.display = "block";
    document.getElementById("lat-display").textContent = lat.toFixed(6);
    document.getElementById("lng-display").textContent = lng.toFixed(6);
  }
}

document.addEventListener("DOMContentLoaded", function () {
  // Initialize both views to be active simultaneously
  const listView = document.getElementById("list-view");
  const mapView = document.getElementById("map-view");

  if (listView) listView.classList.add("active-view");
  if (mapView) mapView.classList.add("active-view");

  // Filter panel expand/collapse functionality
  const filterPanel = document.getElementById("filter-panel");
  const filterHeader = document.querySelector(".filter-header");
  const toggleFiltersBtn = document.getElementById("toggle-filters");

  function toggleFilterPanel() {
    if (filterPanel.classList.contains("collapsed")) {
      filterPanel.classList.remove("collapsed");
      filterPanel.classList.add("expanded");
    } else {
      filterPanel.classList.remove("expanded");
      filterPanel.classList.add("collapsed");
    }

    // Resize map after animation completes
    setTimeout(() => {
      if (searchMap) {
        searchMap.invalidateSize(true);
      }
    }, 300);
  }

  // Add click event to both header and toggle button
  if (filterHeader) {
    filterHeader.addEventListener("click", function (e) {
      // Prevent click if they clicked the toggle button directly
      if (
        e.target !== toggleFiltersBtn &&
        !toggleFiltersBtn.contains(e.target)
      ) {
        toggleFilterPanel();
      }
    });
  }

  if (toggleFiltersBtn) {
    toggleFiltersBtn.addEventListener("click", function (e) {
      e.stopPropagation(); // Prevent double toggle from header click
      toggleFilterPanel();
    });
  }

  // Advanced filters modal functionality
  const advancedFiltersBtn = document.getElementById("advanced-filters-btn");
  const advancedFiltersModal = new bootstrap.Modal(
    document.getElementById("advanced-filters-modal")
  );

  if (advancedFiltersBtn) {
    advancedFiltersBtn.addEventListener("click", function () {
      advancedFiltersModal.show();
    });
  }

  // Apply advanced filters button - transfer values from modal to hidden form fields
  const applyAdvancedFiltersBtn = document.getElementById(
    "apply-advanced-filters"
  );
  if (applyAdvancedFiltersBtn) {
    applyAdvancedFiltersBtn.addEventListener("click", function () {
      // Booking type
      const filterType =
        document.querySelector('input[name="filter_type_modal"]:checked')
          ?.value || "single";
      document.getElementById("filter_type_hidden").value = filterType;

      // EV Charger options
      const hasEvCharger = document.getElementById("ev_charger").checked
        ? "on"
        : "";
      document.getElementById("has_ev_charger_hidden").value = hasEvCharger;

      if (hasEvCharger) {
        const chargerLevel = document.getElementById("charger_level").value;
        const connectorType = document.getElementById("connector_type").value;
        document.getElementById("charger_level_hidden").value = chargerLevel;
        document.getElementById("connector_type_hidden").value = connectorType;
      }

      // Date and time for single booking
      if (filterType === "single") {
        const startDate = document.getElementById("single_start_date").value;
        const endDate = document.getElementById("single_end_date").value;
        const startTime = document.getElementById("start_time_select").value;
        const endTime = document.getElementById("end_time_select").value;

        document.getElementById("start_date_hidden").value = startDate;
        document.getElementById("end_date_hidden").value = endDate;
        document.getElementById("start_time_hidden").value = startTime;
        document.getElementById("end_time_hidden").value = endTime;
      }
      // Recurring booking details
      else if (filterType === "recurring") {
        const recurringStartDate = document.getElementById(
          "recurring_start_date"
        ).value;
        const recurringStartTime = document.getElementById(
          "recurring_start_time"
        ).value;
        const recurringEndTime =
          document.getElementById("recurring_end_time").value;
        const recurringPattern =
          document.querySelector(
            'input[name="recurring_pattern_modal"]:checked'
          )?.value || "daily";

        document.getElementById("recurring_start_date_hidden").value =
          recurringStartDate;
        document.getElementById("recurring_start_time_hidden").value =
          recurringStartTime;
        document.getElementById("recurring_end_time_hidden").value =
          recurringEndTime;
        document.getElementById("recurring_pattern_hidden").value =
          recurringPattern;

        if (recurringPattern === "daily") {
          const recurringEndDate =
            document.getElementById("recurring_end_date").value;
          document.getElementById("recurring_end_date_hidden").value =
            recurringEndDate;
        } else if (recurringPattern === "weekly") {
          const recurringWeeks =
            document.getElementById("recurring_weeks").value;
          document.getElementById("recurring_weeks_hidden").value =
            recurringWeeks;
        }

        const recurringOvernight = document.getElementById(
          "recurring_overnight"
        ).checked
          ? "on"
          : "";
        document.getElementById("recurring_overnight_hidden").value =
          recurringOvernight;
      }

      // Close the modal
      advancedFiltersModal.hide();
    });
  }

  // Existing code for radius toggle functionality
  const enableRadiusCheckbox = document.getElementById("enable-radius");
  const radiusInputGroup = document.getElementById("radius-input-group");
  const radiusHint = document.getElementById("radius-hint");

  if (enableRadiusCheckbox && radiusInputGroup && radiusHint) {
    enableRadiusCheckbox.addEventListener("change", function () {
      radiusInputGroup.style.display = this.checked ? "flex" : "none";
      radiusHint.style.display = this.checked ? "none" : "block";
    });
  }

  // Modal-specific form controls

  // Date range toggle
  const dateRangeToggle = document.getElementById("date-range-toggle");
  const endDateContainer = document.getElementById("end-date-container");

  if (dateRangeToggle && endDateContainer) {
    dateRangeToggle.addEventListener("click", function () {
      if (endDateContainer.style.display === "none") {
        endDateContainer.style.display = "block";
        this.classList.add("active");
      } else {
        endDateContainer.style.display = "none";
        this.classList.remove("active");
      }
    });
  }

  // Booking type toggle
  const filterSingle = document.getElementById("filter_single");
  const filterRecurring = document.getElementById("filter_recurring");
  const singleFilter = document.getElementById("single-filter");
  const recurringFilter = document.getElementById("recurring-filter");

  if (filterSingle && filterRecurring && singleFilter && recurringFilter) {
    function updateBookingTypeVisibility() {
      if (filterSingle.checked) {
        singleFilter.style.display = "block";
        recurringFilter.style.display = "none";
      } else {
        singleFilter.style.display = "none";
        recurringFilter.style.display = "block";
      }
    }

    filterSingle.addEventListener("change", updateBookingTypeVisibility);
    filterRecurring.addEventListener("change", updateBookingTypeVisibility);
  }

  // EV charger toggle
  const evChargerCheckbox = document.getElementById("ev_charger");
  const evOptionsContainer = document.getElementById("ev-options-container");

  if (evChargerCheckbox && evOptionsContainer) {
    evChargerCheckbox.addEventListener("change", function () {
      evOptionsContainer.style.display = this.checked ? "block" : "none";
    });
  }

  // Recurring pattern toggle functionality
  const patternDailyRadio = document.getElementById("pattern_daily");
  const patternWeeklyRadio = document.getElementById("pattern_weekly");
  const dailyPatternFields = document.getElementById("daily-pattern-fields");
  const weeklyPatternFields = document.getElementById("weekly-pattern-fields");

  if (
    patternDailyRadio &&
    patternWeeklyRadio &&
    dailyPatternFields &&
    weeklyPatternFields
  ) {
    patternDailyRadio.addEventListener("change", function () {
      if (this.checked) {
        dailyPatternFields.style.display = "block";
        weeklyPatternFields.style.display = "none";
      }
    });

    patternWeeklyRadio.addEventListener("change", function () {
      if (this.checked) {
        dailyPatternFields.style.display = "none";
        weeklyPatternFields.style.display = "block";
      }
    });
  }

  // Initialize map directly since it's always visible
  initializeMap();

  // Force map resize immediately AND after a short delay
  setTimeout(() => {
    if (searchMap) {
      searchMap.invalidateSize(true);
    }

    // Fix any initial spacing issues with the layout
    const mainContent = document.getElementById("main-content");
    if (mainContent) {
      mainContent.style.position = "absolute";
      mainContent.style.top = "56px"; // Match navbar height
      mainContent.style.left = "0";
      mainContent.style.right = "0";
      mainContent.style.bottom = "0";
    }
  }, 100);

  // Add window resize handler to ensure map fills space correctly
  window.addEventListener("resize", function () {
    if (searchMap) {
      searchMap.invalidateSize(true);
    }
  });
});
