"use client";

import { useEffect, useRef, useState, useMemo } from "react";
import { Map, NavigationControl, ScaleControl, FullscreenControl, GeolocateControl } from "maplibre-gl";
import "maplibre-gl/dist/maplibre-gl.css";
import { Deck } from "@deck.gl/react";
import { GeoJsonLayer, ScatterplotLayer, PolygonLayer, HexagonLayer } from "@deck.gl/layers";
import { useAuthStore } from "@/lib/stores/authStore";
import { spatialApi, hazardApi, sitesApi, prioritizationApi } from "@/lib/api";
import { getSeverityColor, getPriorityColor, getHazardTypeColor } from "@/lib/utils";
import type { HazardZone, RelocationSite, RelocationPriority, Habitation } from "@/types";

interface MapViewProps {
  initialViewport?: {
    longitude: number;
    latitude: number;
    zoom: number;
  };
}

const INITIAL_VIEWPORT = {
  longitude: 78.9629,
  latitude: 20.5937,
  zoom: 4.5,
  pitch: 0,
  bearing: 0,
};

export function MapView({ initialViewport = INITIAL_VIEWPORT }: MapViewProps) {
  const mapContainerRef = useRef<HTMLDivElement>(null);
  const deckRef = useRef<Deck>(null);
  const mapRef = useRef<Map | null>(null);
  const [viewport, setViewport] = useState(initialViewport);
  const [layers, setLayers] = useState<{
    redZones: HazardZone[];
    sites: RelocationSite[];
    priorities: RelocationPriority[];
    habitations: Habitation[];
  }>({
    redZones: [],
    sites: [],
    priorities: [],
    habitations: [],
  });
  const [layerVisibility, setLayerVisibility] = useState({
    redZones: true,
    sites: true,
    priorities: true,
    habitations: false,
  });
  const [loading, setLoading] = useState(false);
  const { accessToken } = useAuthStore();

  // Initialize MapLibre map
  useEffect(() => {
    if (!mapContainerRef.current || mapRef.current) return;

    const map = new Map({
      container: mapContainerRef.current,
      style: {
        version: 8,
        sources: {
          "osm": {
            type: "raster",
            tiles: [
              "https://a.tile.openstreetmap.org/{z}/{x}/{y}.png",
              "https://b.tile.openstreetmap.org/{z}/{x}/{y}.png",
              "https://c.tile.openstreetmap.org/{z}/{x}/{y}.png",
            ],
            tileSize: 256,
            attribution: "© OpenStreetMap contributors",
          },
        },
        layers: [
          {
            id: "osm",
            type: "raster",
            source: "osm",
            minzoom: 0,
            maxzoom: 19,
          },
        ],
      },
      center: [viewport.longitude, viewport.latitude],
      zoom: viewport.zoom,
      pitch: viewport.pitch,
      bearing: viewport.bearing,
    });

    map.addControl(new NavigationControl(), "top-right");
    map.addControl(new ScaleControl({ unit: "metric" }), "bottom-right");
    map.addControl(new FullscreenControl(), "top-right");
    map.addControl(
      new GeolocateControl({
        positionOptions: { enableHighAccuracy: true },
        trackUserLocation: true,
        showUserLocation: true,
      }),
      "top-right"
    );

    map.on("move", () => {
      const center = map.getCenter();
      setViewport((prev) => ({
        ...prev,
        longitude: center.lng,
        latitude: center.lat,
        zoom: map.getZoom(),
        pitch: map.getPitch(),
        bearing: map.getBearing(),
      }));
    });

    mapRef.current = map;

    return () => {
      map.remove();
      mapRef.current = null;
    };
  }, []);

  // Deck.gl layers
  const deckLayers = useMemo(() => {
    const deckLayers = [];

    // Red Zones Layer
    if (layerVisibility.redZones && layers.redZones.length > 0) {
      deckLayers.push(
        new GeoJsonLayer({
          id: "red-zones",
          data: {
            type: "FeatureCollection",
            features: layers.redZones.map((zone) => ({
              type: "Feature",
              geometry: zone.geom,
              properties: {
                id: zone.id,
                hazard_type: zone.hazard_type,
                severity: zone.severity,
                severity_score: zone.severity_score,
                source: zone.source,
                confidence_score: zone.confidence_score,
              },
            })),
          },
          getFillColor: (f) => {
            const severity = f.properties.severity as SeverityLevel;
            const color = getSeverityColor(severity);
            return hexToRgb(color, 0.6);
          },
          getLineColor: (f) => {
            const severity = f.properties.severity as SeverityLevel;
            const color = getSeverityColor(severity);
            return hexToRgb(color, 1);
          },
          getLineWidth: 2,
          lineWidthMinPixels: 1,
          pickable: true,
          autoHighlight: true,
          highlightColor: [255, 255, 0, 180],
        })
      );
    }

    // Relocation Sites Layer
    if (layerVisibility.sites && layers.sites.length > 0) {
      deckLayers.push(
        new ScatterplotLayer({
          id: "relocation-sites",
          data: layers.sites,
          getPosition: (d) => {
            const geom = d.geom as GeoJSON.Geometry;
            if (geom.type === "Polygon") {
              const coords = geom.coordinates[0];
              const center = coords.reduce(
                (acc: number[], coord: number[]) => [acc[0] + coord[0], acc[1] + coord[1]],
                [0, 0]
              );
              return [center[0] / coords.length, center[1] / coords.length];
            }
            return [0, 0];
          },
          getRadius: (d) => Math.max(500, (d.max_carrying_capacity || 100) * 10),
          getFillColor: (d) => {
            const score = d.composite_suitability_score || 50;
            const r = Math.round(255 * (1 - score / 100));
            const g = Math.round(255 * (score / 100));
            return [r, g, 0, 180];
          },
          getLineColor: [255, 255, 255],
          getLineWidth: 2,
          radiusMinPixels: 5,
          radiusMaxPixels: 100,
          pickable: true,
          autoHighlight: true,
        })
      );
    }

    // Habitations Layer
    if (layerVisibility.habitations && layers.habitations.length > 0) {
      deckLayers.push(
        new ScatterplotLayer({
          id: "habitations",
          data: layers.habitations,
          getPosition: (d) => {
            const geom = d.geom as GeoJSON.Geometry;
            return geom.coordinates as [number, number];
          },
          getRadius: (d) => Math.max(100, Math.sqrt(d.population || 100) * 10),
          getFillColor: (d) => {
            const vuln = d.composite_vulnerability || 0;
            const r = Math.round(255 * (vuln / 100));
            const g = Math.round(255 * (1 - vuln / 100));
            return [r, g, 0, 200];
          },
          getLineColor: [255, 255, 255],
          getLineWidth: 1,
          radiusMinPixels: 3,
          radiusMaxPixels: 50,
          pickable: true,
          autoHighlight: true,
        })
      );
    }

    // Priority Flows Layer
    if (layerVisibility.priorities && layers.priorities.length > 0 && layers.sites.length > 0) {
      const siteMap = new Map(layers.sites.map((s) => [s.id, s]));
      
      deckLayers.push(
        new GeoJsonLayer({
          id: "priority-flows",
          data: {
            type: "FeatureCollection",
            features: layers.priorities
              .filter((p) => p.recommended_site_id && siteMap.has(p.recommended_site_id))
              .map((p) => {
                const hab = layers.habitations.find((h) => h.id === p.habitation_id);
                const site = siteMap.get(p.recommended_site_id!);
                if (!hab || !site) return null;
                
                const habGeom = hab.geom as GeoJSON.Geometry;
                const siteGeom = site.geom as GeoJSON.Geometry;
                
                let siteCoords: number[];
                if (siteGeom.type === "Polygon") {
                  const coords = siteGeom.coordinates[0];
                  siteCoords = [
                    coords.reduce((a, c) => a + c[0], 0) / coords.length,
                    coords.reduce((a, c) => a + c[1], 0) / coords.length,
                  ];
                } else {
                  return null;
                }
                
                return {
                  type: "Feature",
                  geometry: {
                    type: "LineString",
                    coordinates: [
                      habGeom.coordinates,
                      siteCoords,
                    ],
                  },
                  properties: {
                    id: p.id,
                    priority_tier: p.priority_tier,
                    habitation_name: hab.name,
                    site_name: site.name,
                  },
                };
              })
              .filter(Boolean),
          },
          getSourcePosition: (f) => f.geometry.coordinates[0],
          getTargetPosition: (f) => f.geometry.coordinates[1],
          getSourceColor: (f) => {
            const tier = f.properties.priority_tier as PriorityTier;
            return hexToRgb(getPriorityColor(tier), 0.8);
          },
          getTargetColor: (f) => {
            const tier = f.properties.priority_tier as PriorityTier;
            return hexToRgb(getPriorityColor(tier), 0.8);
          },
          getWidth: 2,
          widthMinPixels: 1,
          pickable: true,
          autoHighlight: true,
        })
      );
    }

    return deckLayers;
  }, [layers, layerVisibility]);

  // Load data
  const loadData = async () => {
    if (!accessToken) return;
    setLoading(true);
    try {
      const [redZonesRes, sitesRes, prioritiesRes, habitationsRes] = await Promise.all([
        hazardApi.getRedZones({ size: 5000 }),
        sitesApi.getSites({ size: 5000 }),
        prioritizationApi.getPriorities({ size: 5000 }),
        spatialApi.getHabitations({ size: 5000 }),
      ]);

      setLayers({
        redZones: redZonesRes.data.items || [],
        sites: sitesRes.data.items || [],
        priorities: prioritiesRes.data.items || [],
        habitations: habitationsRes.data.items || [],
      });
    } catch (error) {
      console.error("Failed to load map data:", error);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadData();
  }, [accessToken]);

  // Render Deck.gl overlay
  useEffect(() => {
    if (!mapRef.current || !mapContainerRef.current) return;

    const deck = new Deck({
      canvas: mapContainerRef.current.querySelector("canvas") || undefined,
      width: "100%",
      height: "100%",
      initialViewState: viewport,
      controller: true,
      layers: deckLayers,
      onViewStateChange: ({ viewState }) => {
        setViewport(viewState);
        if (mapRef.current) {
          mapRef.current.jumpTo({
            center: [viewState.longitude, viewState.latitude],
            zoom: viewState.zoom,
            pitch: viewState.pitch,
            bearing: viewState.bearing,
          });
        }
      },
    });

    deckRef.current = deck;

    return () => {
      deck.finalize();
    };
  }, [deckLayers, viewport]);

  const toggleLayer = (layer: keyof typeof layerVisibility) => {
    setLayerVisibility((prev) => ({ ...prev, [layer]: !prev[layer] }));
  };

  if (!mapContainerRef.current) return null;

  return (
    <div ref={mapContainerRef} className="relative w-full h-full">
      {/* MapLibre Map */}
      <div className="absolute inset-0" />
      
      {/* Layer Controls */}
      <div className="absolute top-4 left-4 z-10 bg-white dark:bg-gray-800 rounded-lg shadow-lg p-3 border border-gray-200 dark:border-gray-700">
        <div className="font-medium text-sm mb-2">Map Layers</div>
        <div className="space-y-2">
          {[
            { key: "redZones", label: "Red Zones", color: "#F44336" },
            { key: "sites", label: "Relocation Sites", color: "#4CAF50" },
            { key: "priorities", label: "Priority Flows", color: "#2196F3" },
            { key: "habitations", label: "Habitations", color: "#FF9800" },
          ].map(({ key, label, color }) => (
            <label key={key} className="flex items-center gap-2 cursor-pointer">
              <input
                type="checkbox"
                checked={layerVisibility[key as keyof typeof layerVisibility]}
                onChange={() => toggleLayer(key as keyof typeof layerVisibility)}
                className="rounded border-gray-300 text-primary focus:ring-primary"
              />
              <span className="flex items-center gap-1 text-sm">
                <span className="w-3 h-3 rounded" style={{ backgroundColor: color }} />
                {label}
              </span>
            </label>
          ))}
        </div>
      </div>

      {/* Loading indicator */}
      {loading && (
        <div className="absolute top-4 right-4 z-10 bg-white dark:bg-gray-800 rounded-lg shadow-lg px-4 py-2 border border-gray-200 dark:border-gray-700">
          <div className="flex items-center gap-2">
            <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-primary" />
            <span className="text-sm">Loading map data...</span>
          </div>
        </div>
      )}

      {/* Legend */}
      <div className="absolute bottom-4 left-4 z-10 bg-white dark:bg-gray-800 rounded-lg shadow-lg p-3 border border-gray-200 dark:border-gray-700 max-w-xs">
        <div className="font-medium text-sm mb-2">Legend</div>
        <div className="space-y-1 text-xs">
          <div className="flex items-center gap-2">
            <div className="w-4 h-4 rounded" style={{ backgroundColor: "rgba(244, 67, 54, 0.6)" }} />
            <span>Red Zones (High/Very High)</span>
          </div>
          <div className="flex items-center gap-2">
            <div className="w-4 h-4 rounded" style={{ backgroundColor: "rgba(76, 175, 80, 0.7)" }} />
            <span>Relocation Sites</span>
          </div>
          <div className="flex items-center gap-2">
            <div className="w-4 h-4 rounded" style={{ backgroundColor: "rgba(255, 152, 0, 0.8)" }} />
            <span>Habitations (by vulnerability)</span>
          </div>
          <div className="flex items-center gap-2">
            <svg width="16" height="16" viewBox="0 0 16 16">
              <line x1="0" y1="8" x2="16" y2="8" stroke="#2196F3" strokeWidth="2" strokeDasharray="4,4" />
            </svg>
            <span>Priority Flows</span>
          </div>
        </div>
      </div>
    </div>
  );
}

function hexToRgb(hex: string, alpha: number): [number, number, number, number] {
  const result = /^#?([a-f\d]{2})([a-f\d]{2})([a-f\d]{2})$/i.exec(hex);
  if (!result) return [128, 128, 128, Math.round(alpha * 255)];
  return [
    parseInt(result[1], 16),
    parseInt(result[2], 16),
    parseInt(result[3], 16),
    Math.round(alpha * 255),
  ];
}