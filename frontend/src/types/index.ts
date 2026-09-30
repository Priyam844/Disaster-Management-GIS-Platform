// Base types
export interface BaseEntity {
  id: string;
  created_at: string;
  updated_at: string;
}

// Pagination
export interface PaginationParams {
  page: number;
  size: number;
}

export interface PaginatedResponse<T> {
  items: T[];
  total: number;
  page: number;
  size: number;
  pages: number;
}

// Auth types
export interface User {
  id: string;
  email: string;
  username: string;
  full_name: string | null;
  role: UserRole;
  is_active: boolean;
  is_superuser: boolean;
  last_login: string | null;
  metadata: Record<string, unknown>;
  created_at: string;
  updated_at: string;
  permitted_states: PermittedState[];
}

export type UserRole = "ADMIN" | "ANALYST" | "VIEWER";

export interface PermittedState {
  id: string;
  name: string;
  code: string;
}

export interface Token {
  access_token: string;
  refresh_token: string;
  token_type: string;
  expires_in: number;
}

export interface LoginRequest {
  username: string;
  password: string;
}

export interface UserCreate {
  email: string;
  username: string;
  password: string;
  full_name?: string;
  role?: UserRole;
  permitted_state_ids?: string[];
}

export interface UserUpdate {
  email?: string;
  username?: string;
  full_name?: string;
  role?: UserRole;
  is_active?: boolean;
  permitted_state_ids?: string[];
}

// Spatial types
export interface State extends BaseEntity {
  name: string;
  code: string;
  geom: GeoJSON.Geometry;
  metadata: Record<string, unknown>;
}

export interface District extends BaseEntity {
  state_id: string;
  name: string;
  code: string;
  geom: GeoJSON.Geometry;
  metadata: Record<string, unknown>;
  state?: State;
}

export interface Habitation extends BaseEntity {
  district_id: string;
  state_id: string;
  name: string;
  geom: GeoJSON.Geometry;
  boundary_geom?: GeoJSON.Geometry;
  population: number | null;
  households: number | null;
  socioeconomic_vulnerability: number | null;
  physical_vulnerability: number | null;
  composite_vulnerability: number | null;
  literacy_rate: number | null;
  pucca_houses_pct: number | null;
  sc_st_pct: number | null;
  female_headed_pct: number | null;
  disability_pct: number | null;
  road_access_km: number | null;
  healthcare_access_km: number | null;
  metadata: Record<string, unknown>;
  assessed_at: string | null;
  district?: District;
  state?: State;
}

export type HazardType = "LANDSLIDE" | "FLOOD" | "COASTAL_EROSION" | "CLOUDBURST" | "EARTHQUAKE";
export type SeverityLevel = "VERY_LOW" | "LOW" | "MODERATE" | "HIGH" | "VERY_HIGH";

export interface HazardZone extends BaseEntity {
  hazard_type: HazardType;
  severity: SeverityLevel;
  severity_score: number | null;
  geom: GeoJSON.Geometry;
  valid_from: string;
  valid_to: string | null;
  source: string;
  model_version: string | null;
  confidence_score: number | null;
  metadata: Record<string, unknown>;
}

export interface DisasterEvent extends BaseEntity {
  hazard_type: HazardType;
  event_name: string | null;
  event_date: string;
  end_date: string | null;
  affected_geom: GeoJSON.Geometry | null;
  affected_habitations: string[];
  casualties: number | null;
  injured: number | null;
  displaced: number | null;
  houses_damaged: number | null;
  economic_loss_inr: number | null;
  source: string | null;
  verified: boolean;
  metadata: Record<string, unknown>;
}

export type PriorityTier = "IMMEDIATE" | "SHORT_TERM" | "MEDIUM_TERM" | "NOT_REQUIRED";
export type RelocationStatus = "PENDING" | "IN_PROGRESS" | "COMPLETED" | "ON_HOLD" | "CANCELLED";

export interface RelocationSite extends BaseEntity {
  district_id: string;
  name: string;
  geom: GeoJSON.Geometry;
  total_area_ha: number;
  buildable_area_ha: number | null;
  agricultural_area_ha: number | null;
  forest_area_ha: number | null;
  water_body_area_ha: number | null;
  water_availability_score: number | null;
  road_access_score: number | null;
  electricity_access: boolean;
  healthcare_facility_km: number | null;
  school_facility_km: number | null;
  market_facility_km: number | null;
  current_population: number;
  max_carrying_capacity: number | null;
  recommended_capacity: number | null;
  land_suitability_score: number | null;
  water_suitability_score: number | null;
  infrastructure_suitability_score: number | null;
  environmental_suitability_score: number | null;
  composite_suitability_score: number | null;
  flood_risk: boolean;
  landslide_risk: boolean;
  seismic_zone: number | null;
  ecological_sensitivity: string | null;
  land_ownership: string | null;
  assessment_date: string;
  assessed_by: string | null;
  metadata: Record<string, unknown>;
  district?: District;
}

export interface RelocationPriority extends BaseEntity {
  habitation_id: string;
  recommended_site_id: string | null;
  alternative_site_ids: string[];
  priority_tier: PriorityTier;
  priority_rank: number | null;
  hazard_exposure_score: number | null;
  vulnerability_score: number | null;
  capacity_gap_score: number | null;
  distance_score: number | null;
  cost_effectiveness_score: number | null;
  composite_priority_score: number | null;
  distance_to_site_km: number | null;
  estimated_relocation_cost_inr: number | null;
  estimated_timeline_months: number | null;
  status: RelocationStatus;
  approved_by: string | null;
  approved_at: string | null;
  notes: string | null;
  model_version: string | null;
  computed_at: string;
  habitation?: Habitation;
  recommended_site?: RelocationSite;
}

export interface SiteCapacityResponse {
  site_id: string;
  site_name: string;
  max_carrying_capacity: number | null;
  recommended_capacity: number | null;
  current_population: number;
  available_capacity: number;
  composite_suitability_score: number | null;
  assigned_habitations: number;
  assigned_population: number;
  capacity_breakdown: Record<string, unknown>;
}

// Filters
export interface HazardZoneFilters {
  hazard_type?: HazardType;
  severity?: SeverityLevel;
  state_code?: string;
  district_code?: string;
  bbox?: string;
  valid_at?: string;
  source?: string;
}

export interface SiteFilters {
  district_id?: string;
  state_code?: string;
  suitability_min?: number;
  capacity_min?: number;
  risk_free?: boolean;
}

export interface PrioritizationFilters {
  state_code?: string;
  district_id?: string;
  tier?: PriorityTier;
  site_id?: string;
  status?: RelocationStatus;
  min_score?: number;
}

// Analytics
export interface DashboardSummary {
  total_habitations: number;
  total_population: number;
  high_vulnerability_habitations: number;
  active_red_zones: number;
  total_relocation_sites: number;
  total_capacity: number;
  immediate_priority_count: number;
  short_term_priority_count: number;
  medium_term_priority_count: number;
  population_at_risk: number;
}

export interface HazardTrendPoint {
  date: string;
  hazard_type: HazardType;
  count: number;
  affected_population: number;
}

export interface VulnerabilityDistribution {
  range: string;
  count: number;
  percentage: number;
}

export interface CapacityGapAnalysis {
  district_id: string;
  district_name: string;
  demand_population: number;
  available_capacity: number;
  gap: number;
  gap_percentage: number;
}

// Export
export interface ExportRequest {
  format: "geojson" | "csv" | "pdf";
  filters?: Record<string, unknown>;
}

// Map types
export interface MapLayer {
  id: string;
  type: "fill" | "line" | "circle" | "heatmap" | "symbol";
  source: string;
  paint?: Record<string, unknown>;
  layout?: Record<string, unknown>;
  filter?: unknown[];
}

export interface MapViewport {
  longitude: number;
  latitude: number;
  zoom: number;
  pitch?: number;
  bearing?: number;
}

export interface MapBounds {
  minLng: number;
  minLat: number;
  maxLng: number;
  maxLat: number;
}