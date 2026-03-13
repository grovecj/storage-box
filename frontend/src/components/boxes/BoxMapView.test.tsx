import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import BoxMapView from "./BoxMapView";
import type { StorageBox } from "@/types";

// Mock react-leaflet
vi.mock("react-leaflet", () => ({
  MapContainer: ({ children }: { children: React.ReactNode }) => (
    <div data-testid="map-container">{children}</div>
  ),
  TileLayer: () => <div data-testid="tile-layer" />,
  Marker: ({ children }: { children: React.ReactNode }) => (
    <div data-testid="map-marker">{children}</div>
  ),
  Popup: ({ children }: { children: React.ReactNode }) => (
    <div data-testid="map-popup">{children}</div>
  ),
  useMap: () => ({ fitBounds: vi.fn(), setView: vi.fn() }),
}));

// Mock leaflet
vi.mock("leaflet", () => ({
  default: {
    Icon: { Default: { prototype: {}, mergeOptions: vi.fn() } },
  },
  LatLngBounds: class LatLngBounds {
    constructor() {
      return {} as never;
    }
  },
}));

const geoBox: StorageBox = {
  id: 1,
  box_code: "BOX-0001",
  name: "Kitchen Stuff",
  latitude: 47.6062,
  longitude: -122.3321,
  location_name: "Seattle Apartment",
  item_count: 5,
  created_at: "2026-01-01T00:00:00Z",
  updated_at: "2026-01-01T00:00:00Z",
  created_by: 1,
  updated_by: 1,
};

const geoBox2: StorageBox = {
  id: 2,
  box_code: "BOX-0002",
  name: "Office Supplies",
  latitude: 47.6205,
  longitude: -122.3493,
  location_name: "Downtown Office",
  item_count: 12,
  created_at: "2026-01-02T00:00:00Z",
  updated_at: "2026-01-02T00:00:00Z",
  created_by: 1,
  updated_by: 1,
};

const geoBoxNoLocation: StorageBox = {
  id: 3,
  box_code: "BOX-0003",
  name: "Books",
  latitude: 47.6155,
  longitude: -122.3200,
  location_name: null,
  item_count: 8,
  created_at: "2026-01-03T00:00:00Z",
  updated_at: "2026-01-03T00:00:00Z",
  created_by: 1,
  updated_by: 1,
};

const nonGeoBox: StorageBox = {
  id: 4,
  box_code: "BOX-0004",
  name: "Winter Clothes",
  latitude: null,
  longitude: null,
  location_name: "Mom's Garage",
  item_count: 12,
  created_at: "2026-01-04T00:00:00Z",
  updated_at: "2026-01-04T00:00:00Z",
  created_by: 1,
  updated_by: 1,
};

const nonGeoBox2: StorageBox = {
  id: 5,
  box_code: "BOX-0005",
  name: "Summer Gear",
  latitude: null,
  longitude: null,
  location_name: null,
  item_count: 7,
  created_at: "2026-01-05T00:00:00Z",
  updated_at: "2026-01-05T00:00:00Z",
  created_by: 1,
  updated_by: 1,
};

const singleItemBox: StorageBox = {
  id: 6,
  box_code: "BOX-0006",
  name: "Single Item Box",
  latitude: 47.6100,
  longitude: -122.3300,
  location_name: "Storage Unit",
  item_count: 1,
  created_at: "2026-01-06T00:00:00Z",
  updated_at: "2026-01-06T00:00:00Z",
  created_by: 1,
  updated_by: 1,
};

describe("BoxMapView", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("renders empty state when no boxes have coordinates", () => {
    render(
      <MemoryRouter>
        <BoxMapView boxes={[nonGeoBox, nonGeoBox2]} />
      </MemoryRouter>
    );

    expect(screen.getByText(/no boxes have location data yet/i)).toBeInTheDocument();
    expect(screen.getByText(/use "set location" on box detail pages/i)).toBeInTheDocument();
    expect(screen.queryByTestId("map-container")).not.toBeInTheDocument();
  });

  it("renders map with markers when boxes have coordinates", () => {
    render(
      <MemoryRouter>
        <BoxMapView boxes={[geoBox, geoBox2]} />
      </MemoryRouter>
    );

    expect(screen.getByTestId("map-container")).toBeInTheDocument();
    expect(screen.getByTestId("tile-layer")).toBeInTheDocument();

    const markers = screen.getAllByTestId("map-marker");
    expect(markers).toHaveLength(2);
  });

  it("shows correct count of geolocated boxes", () => {
    render(
      <MemoryRouter>
        <BoxMapView boxes={[geoBox, geoBox2]} />
      </MemoryRouter>
    );

    expect(screen.getByText(/showing 2 geolocated boxes/i)).toBeInTheDocument();
  });

  it("renders non-geolocated boxes list below map", () => {
    render(
      <MemoryRouter>
        <BoxMapView boxes={[geoBox, nonGeoBox]} />
      </MemoryRouter>
    );

    expect(screen.getByText(/boxes without location \(1\)/i)).toBeInTheDocument();
    expect(screen.getByText(nonGeoBox.box_code)).toBeInTheDocument();
    expect(screen.getByText(nonGeoBox.name)).toBeInTheDocument();
  });

  it('shows "Boxes Without Location" section header with count', () => {
    render(
      <MemoryRouter>
        <BoxMapView boxes={[geoBox, nonGeoBox, nonGeoBox2]} />
      </MemoryRouter>
    );

    expect(screen.getByText(/boxes without location \(2\)/i)).toBeInTheDocument();
  });

  it("each non-geolocated box links to /boxes/{id}", () => {
    render(
      <MemoryRouter>
        <BoxMapView boxes={[nonGeoBox]} />
      </MemoryRouter>
    );

    const link = screen.getByRole("link", { name: new RegExp(nonGeoBox.name, "i") });
    expect(link).toHaveAttribute("href", `/boxes/${nonGeoBox.id}`);
  });

  it("marker popups contain box code, name, item count", () => {
    render(
      <MemoryRouter>
        <BoxMapView boxes={[geoBox]} />
      </MemoryRouter>
    );

    const popup = screen.getByTestId("map-popup");
    expect(popup).toHaveTextContent(geoBox.box_code);
    expect(popup).toHaveTextContent(geoBox.name);
    expect(popup).toHaveTextContent(`${geoBox.item_count} items`);
  });

  it("marker popups contain View Box link to correct URL", () => {
    render(
      <MemoryRouter>
        <BoxMapView boxes={[geoBox]} />
      </MemoryRouter>
    );

    const viewBoxLink = screen.getByRole("link", { name: /view box/i });
    expect(viewBoxLink).toHaveAttribute("href", `/boxes/${geoBox.id}`);
  });

  it("shows location_name in popup when available", () => {
    render(
      <MemoryRouter>
        <BoxMapView boxes={[geoBox]} />
      </MemoryRouter>
    );

    const popup = screen.getByTestId("map-popup");
    expect(popup).toHaveTextContent(geoBox.location_name as string);
  });

  it("does not show location_name in popup when null", () => {
    render(
      <MemoryRouter>
        <BoxMapView boxes={[geoBoxNoLocation]} />
      </MemoryRouter>
    );

    const popup = screen.getByTestId("map-popup");
    expect(popup).not.toHaveTextContent("Seattle Apartment");
    expect(popup).toHaveTextContent(geoBoxNoLocation.box_code);
  });

  it("handles mixed boxes (some with coords, some without)", () => {
    render(
      <MemoryRouter>
        <BoxMapView boxes={[geoBox, geoBox2, nonGeoBox, nonGeoBox2]} />
      </MemoryRouter>
    );

    // Map section should show
    expect(screen.getByTestId("map-container")).toBeInTheDocument();
    expect(screen.getByText(/showing 2 geolocated boxes/i)).toBeInTheDocument();

    // Non-geo section should show
    expect(screen.getByText(/boxes without location \(2\)/i)).toBeInTheDocument();
    expect(screen.getByText(nonGeoBox.name)).toBeInTheDocument();
    expect(screen.getByText(nonGeoBox2.name)).toBeInTheDocument();
  });

  it("handles single geolocated box (no plural)", () => {
    render(
      <MemoryRouter>
        <BoxMapView boxes={[geoBox]} />
      </MemoryRouter>
    );

    expect(screen.getByText(/showing 1 geolocated box$/i)).toBeInTheDocument();
  });

  it("uses singular 'item' for box with 1 item", () => {
    render(
      <MemoryRouter>
        <BoxMapView boxes={[singleItemBox]} />
      </MemoryRouter>
    );

    const popup = screen.getByTestId("map-popup");
    expect(popup).toHaveTextContent("1 item");
    expect(popup).not.toHaveTextContent("1 items");
  });

  it("displays item count in non-geolocated boxes list", () => {
    render(
      <MemoryRouter>
        <BoxMapView boxes={[nonGeoBox]} />
      </MemoryRouter>
    );

    expect(screen.getByText(nonGeoBox.item_count.toString())).toBeInTheDocument();
  });

  it("displays location_name in non-geolocated boxes list when available", () => {
    render(
      <MemoryRouter>
        <BoxMapView boxes={[nonGeoBox]} />
      </MemoryRouter>
    );

    expect(screen.getByText(nonGeoBox.location_name as string)).toBeInTheDocument();
  });

  it("does not display location_name in non-geolocated boxes list when null", () => {
    render(
      <MemoryRouter>
        <BoxMapView boxes={[nonGeoBox2]} />
      </MemoryRouter>
    );

    expect(screen.queryByText("Mom's Garage")).not.toBeInTheDocument();
  });

  it("does not show non-geolocated section when all boxes have coordinates", () => {
    render(
      <MemoryRouter>
        <BoxMapView boxes={[geoBox, geoBox2]} />
      </MemoryRouter>
    );

    expect(screen.queryByText(/boxes without location/i)).not.toBeInTheDocument();
  });

  it("renders all geolocated boxes as markers", () => {
    const manyGeoBoxes = [geoBox, geoBox2, geoBoxNoLocation];

    render(
      <MemoryRouter>
        <BoxMapView boxes={manyGeoBoxes} />
      </MemoryRouter>
    );

    const markers = screen.getAllByTestId("map-marker");
    expect(markers).toHaveLength(3);
    expect(screen.getByText(/showing 3 geolocated boxes/i)).toBeInTheDocument();
  });

  it("renders empty array of boxes without error", () => {
    render(
      <MemoryRouter>
        <BoxMapView boxes={[]} />
      </MemoryRouter>
    );

    expect(screen.getByText(/no boxes have location data yet/i)).toBeInTheDocument();
  });

  it("shows truncation warning when total exceeds displayed boxes", () => {
    render(
      <MemoryRouter>
        <BoxMapView boxes={[geoBox, geoBox2]} total={150} />
      </MemoryRouter>
    );

    expect(screen.getByText(/showing 2 of 150 total boxes/i)).toBeInTheDocument();
  });

  it("does not show truncation warning when all boxes are displayed", () => {
    render(
      <MemoryRouter>
        <BoxMapView boxes={[geoBox, geoBox2]} total={2} />
      </MemoryRouter>
    );

    expect(screen.queryByText(/total boxes/i)).not.toBeInTheDocument();
  });
});
