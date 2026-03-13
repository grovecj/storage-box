import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { MemoryRouter } from "react-router-dom";
import Dashboard from "./Dashboard";
import type { BoxListResponse } from "@/types";

// Mock API client
vi.mock("@/api/client", () => ({
  listBoxes: vi.fn(),
}));

// Mock useGeolocation hook
vi.mock("@/hooks/useGeolocation", () => ({
  useGeolocation: () => ({
    latitude: null,
    longitude: null,
    error: null,
    requestLocation: vi.fn(),
  }),
}));

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
  useMap: () => ({ fitBounds: vi.fn() }),
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

// Mock react-router-dom's useNavigate
vi.mock("react-router-dom", async () => {
  const actual = await vi.importActual("react-router-dom");
  return {
    ...actual,
    useNavigate: () => vi.fn(),
  };
});

import { listBoxes } from "@/api/client";

const mockBoxListResponse: BoxListResponse = {
  boxes: [
    {
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
    },
    {
      id: 2,
      box_code: "BOX-0002",
      name: "Winter Clothes",
      latitude: null,
      longitude: null,
      location_name: "Mom's Garage",
      item_count: 12,
      created_at: "2026-01-02T00:00:00Z",
      updated_at: "2026-01-02T00:00:00Z",
      created_by: 1,
      updated_by: 1,
    },
  ],
  total: 2,
  page: 1,
  page_size: 20,
};

const emptyBoxListResponse: BoxListResponse = {
  boxes: [],
  total: 0,
  page: 1,
  page_size: 20,
};

describe("Dashboard - Map View", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    vi.mocked(listBoxes).mockResolvedValue({
      data: mockBoxListResponse,
      status: 200,
      statusText: "OK",
      headers: {},
      config: {} as never,
    });
  });

  it("renders Grid/Map toggle buttons", async () => {
    render(
      <MemoryRouter>
        <Dashboard />
      </MemoryRouter>
    );

    await waitFor(() => {
      expect(screen.getByRole("button", { name: /grid/i })).toBeInTheDocument();
      expect(screen.getByRole("button", { name: /map/i })).toBeInTheDocument();
    });
  });

  it("grid view is active by default", async () => {
    render(
      <MemoryRouter>
        <Dashboard />
      </MemoryRouter>
    );

    await waitFor(() => {
      const gridButton = screen.getByRole("button", { name: /grid/i });
      expect(gridButton).toHaveClass("bg-amber-500");
    });
  });

  it("clicking Map button switches to map view (renders BoxMapView)", async () => {
    const user = userEvent.setup();

    render(
      <MemoryRouter>
        <Dashboard />
      </MemoryRouter>
    );

    await waitFor(() => {
      expect(screen.getByRole("button", { name: /map/i })).toBeInTheDocument();
    });

    const mapButton = screen.getByRole("button", { name: /map/i });
    await user.click(mapButton);

    await waitFor(() => {
      expect(mapButton).toHaveClass("bg-amber-500");
      // BoxMapView should be rendered (look for map-specific content)
      expect(
        screen.getByTestId("map-container") ||
          screen.getByText(/no boxes have location data yet/i)
      ).toBeInTheDocument();
    });
  });

  it("clicking Grid button switches back to grid view", async () => {
    const user = userEvent.setup();

    render(
      <MemoryRouter>
        <Dashboard />
      </MemoryRouter>
    );

    await waitFor(() => {
      expect(screen.getByRole("button", { name: /map/i })).toBeInTheDocument();
    });

    // Switch to map
    const mapButton = screen.getByRole("button", { name: /map/i });
    await user.click(mapButton);

    await waitFor(() => {
      expect(mapButton).toHaveClass("bg-amber-500");
    });

    // Switch back to grid
    const gridButton = screen.getByRole("button", { name: /grid/i });
    await user.click(gridButton);

    await waitFor(() => {
      expect(gridButton).toHaveClass("bg-amber-500");
      expect(mapButton).not.toHaveClass("bg-amber-500");
    });
  });

  it("sort toggle (Recent/Near Me) hidden in map view", async () => {
    const user = userEvent.setup();

    render(
      <MemoryRouter>
        <Dashboard />
      </MemoryRouter>
    );

    await waitFor(() => {
      expect(screen.getByRole("button", { name: /recent/i })).toBeInTheDocument();
    });

    // Switch to map view
    const mapButton = screen.getByRole("button", { name: /map/i });
    await user.click(mapButton);

    await waitFor(() => {
      expect(screen.queryByRole("button", { name: /recent/i })).not.toBeInTheDocument();
      expect(screen.queryByRole("button", { name: /near me/i })).not.toBeInTheDocument();
    });
  });

  it("sort toggle visible in grid view", async () => {
    render(
      <MemoryRouter>
        <Dashboard />
      </MemoryRouter>
    );

    await waitFor(() => {
      expect(screen.getByRole("button", { name: /recent/i })).toBeInTheDocument();
      expect(screen.getByRole("button", { name: /near me/i })).toBeInTheDocument();
    });
  });

  it('"Load More" button only shows in grid view', async () => {
    const user = userEvent.setup();

    // Mock response with more boxes than shown
    vi.mocked(listBoxes).mockResolvedValue({
      data: {
        ...mockBoxListResponse,
        total: 50, // More than page_size
      },
      status: 200,
      statusText: "OK",
      headers: {},
      config: {} as never,
    });

    render(
      <MemoryRouter>
        <Dashboard />
      </MemoryRouter>
    );

    await waitFor(() => {
      expect(screen.getByRole("button", { name: /load more/i })).toBeInTheDocument();
    });

    // Switch to map view
    const mapButton = screen.getByRole("button", { name: /map/i });
    await user.click(mapButton);

    await waitFor(() => {
      expect(screen.queryByRole("button", { name: /load more/i })).not.toBeInTheDocument();
    });
  });

  it("map view fetches all boxes with page_size: 100", async () => {
    const user = userEvent.setup();

    render(
      <MemoryRouter>
        <Dashboard />
      </MemoryRouter>
    );

    await waitFor(() => {
      expect(screen.getByRole("button", { name: /map/i })).toBeInTheDocument();
    });

    // Clear previous calls
    vi.clearAllMocks();

    // Switch to map view
    const mapButton = screen.getByRole("button", { name: /map/i });
    await user.click(mapButton);

    await waitFor(() => {
      expect(listBoxes).toHaveBeenCalledWith(
        expect.objectContaining({
          page: 1,
          page_size: 100,
        })
      );
    });
  });

  it("empty state shown when no boxes exist in map view", async () => {
    const user = userEvent.setup();

    vi.mocked(listBoxes).mockResolvedValue({
      data: emptyBoxListResponse,
      status: 200,
      statusText: "OK",
      headers: {},
      config: {} as never,
    });

    render(
      <MemoryRouter>
        <Dashboard />
      </MemoryRouter>
    );

    await waitFor(() => {
      expect(screen.getByRole("button", { name: /map/i })).toBeInTheDocument();
    });

    // Switch to map view
    const mapButton = screen.getByRole("button", { name: /map/i });
    await user.click(mapButton);

    await waitFor(() => {
      expect(screen.getByText(/no storage boxes yet/i)).toBeInTheDocument();
      expect(screen.getByRole("button", { name: /create your first box/i })).toBeInTheDocument();
    });
  });

  it("shows map container when boxes have coordinates", async () => {
    const user = userEvent.setup();

    render(
      <MemoryRouter>
        <Dashboard />
      </MemoryRouter>
    );

    await waitFor(() => {
      expect(screen.getByRole("button", { name: /map/i })).toBeInTheDocument();
    });

    const mapButton = screen.getByRole("button", { name: /map/i });
    await user.click(mapButton);

    await waitFor(() => {
      expect(screen.getByTestId("map-container")).toBeInTheDocument();
    });
  });

  it("grid view fetches boxes with page_size: 20", async () => {
    render(
      <MemoryRouter>
        <Dashboard />
      </MemoryRouter>
    );

    await waitFor(() => {
      expect(listBoxes).toHaveBeenCalledWith(
        expect.objectContaining({
          page: 1,
          page_size: 20,
        })
      );
    });
  });

  it("displays total count correctly in both views", async () => {
    const user = userEvent.setup();

    vi.mocked(listBoxes).mockResolvedValue({
      data: {
        ...mockBoxListResponse,
        total: 42,
      },
      status: 200,
      statusText: "OK",
      headers: {},
      config: {} as never,
    });

    render(
      <MemoryRouter>
        <Dashboard />
      </MemoryRouter>
    );

    await waitFor(() => {
      expect(screen.getByText("42 boxes")).toBeInTheDocument();
    });

    // Switch to map view - count should remain
    const mapButton = screen.getByRole("button", { name: /map/i });
    await user.click(mapButton);

    await waitFor(() => {
      expect(screen.getByText("42 boxes")).toBeInTheDocument();
    });
  });

  it("displays singular 'box' when total is 1", async () => {
    vi.mocked(listBoxes).mockResolvedValue({
      data: {
        boxes: [mockBoxListResponse.boxes[0]!],
        total: 1,
        page: 1,
        page_size: 20,
      },
      status: 200,
      statusText: "OK",
      headers: {},
      config: {} as never,
    });

    render(
      <MemoryRouter>
        <Dashboard />
      </MemoryRouter>
    );

    await waitFor(() => {
      expect(screen.getByText("1 box")).toBeInTheDocument();
    });
  });

  it("map button is not active when grid is shown", async () => {
    render(
      <MemoryRouter>
        <Dashboard />
      </MemoryRouter>
    );

    await waitFor(() => {
      const mapButton = screen.getByRole("button", { name: /map/i });
      expect(mapButton).not.toHaveClass("bg-amber-500");
    });
  });

  it("grid button is not active when map is shown", async () => {
    const user = userEvent.setup();

    render(
      <MemoryRouter>
        <Dashboard />
      </MemoryRouter>
    );

    await waitFor(() => {
      expect(screen.getByRole("button", { name: /map/i })).toBeInTheDocument();
    });

    const mapButton = screen.getByRole("button", { name: /map/i });
    await user.click(mapButton);

    await waitFor(() => {
      const gridButton = screen.getByRole("button", { name: /grid/i });
      expect(gridButton).not.toHaveClass("bg-amber-500");
    });
  });
});
