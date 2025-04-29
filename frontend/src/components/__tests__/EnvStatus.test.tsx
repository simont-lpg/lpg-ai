import React from "react";
import { render, screen } from "@testing-library/react";
import "@testing-library/jest-dom";
import { EnvStatus } from "../EnvStatus";

jest.mock("../../config", () => ({
  getConfig: () => ({ apiBaseUrl: "http://test-server" }),
}));

describe("EnvStatus", () => {
  beforeEach(() => {
    (global.fetch as jest.Mock).mockImplementation(() =>
      Promise.resolve({
        ok: true,
        json: () =>
          Promise.resolve({
            environment: "development",
            embedding_model: "MiniLM",
            generator_model: "tinyllama:latest",
          }),
      })
    );
  });

  afterEach(() => {
    jest.restoreAllMocks();
  });

  it("renders the environment and model names", async () => {
    render(<EnvStatus />);
    expect(await screen.findByText("Environment: development")).toBeInTheDocument();
    expect(screen.getByText("Embed Model: MiniLM")).toBeInTheDocument();
    expect(screen.getByText("Gen Model: tinyllama:latest")).toBeInTheDocument();
  });
}); 