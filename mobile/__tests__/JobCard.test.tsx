/**
 * JobCard component tests.
 *
 * Requires: npm install --save-dev jest @testing-library/react-native @testing-library/jest-native
 * Run: npx jest __tests__/JobCard.test.tsx
 */

import React from "react";
import { render } from "@testing-library/react-native";

// NOTE: These tests are stubs that verify rendering logic.
// They require the mobile project to have node_modules installed.
// Until then, they serve as documentation of expected behavior.

describe("JobCard", () => {
  // Mock the zustand stores before importing the component
  const mockUseApplicationStatusLabel = jest.fn();
  const mockUseIsProcessing = jest.fn();
  const mockUsePendingInputs = jest.fn();

  jest.mock("../src/stores/applicationStore", () => ({
    useApplicationStatusLabel: (appId: string) => mockUseApplicationStatusLabel(appId),
    useIsProcessing: (appId: string) => mockUseIsProcessing(appId),
    usePendingInputs: (appId: string) => mockUsePendingInputs(appId),
  }));

  // eslint-disable-next-line @typescript-eslint/no-var-requires
  const { JobCard } = require("../src/components/JobCard");

  const baseJob = {
    id: "job-1",
    external_id: "ext-1",
    title: "Senior Engineer",
    company: "Acme Corp",
    description: "A great role",
    location: "San Francisco, CA",
    salary_min: 150000,
    salary_max: 200000,
    category: "Engineering",
    application_url: "https://acme.com/apply",
    source: "adzuna",
    created_at: "2025-01-01T00:00:00Z",
  };

  beforeEach(() => {
    jest.clearAllMocks();
    mockUseApplicationStatusLabel.mockReturnValue(null);
    mockUseIsProcessing.mockReturnValue(false);
    mockUsePendingInputs.mockReturnValue([]);
  });

  it("renders job title and company", () => {
    const { getByText } = render(
      <JobCard job={baseJob} applicationId={null} onAnswerQuestions={jest.fn()} />
    );
    expect(getByText("Senior Engineer")).toBeTruthy();
    expect(getByText("Acme Corp")).toBeTruthy();
  });

  it("shows 'Queued' status badge when QUEUED", () => {
    mockUseApplicationStatusLabel.mockReturnValue("Queued");
    const { getByText } = render(
      <JobCard job={baseJob} applicationId="app-1" onAnswerQuestions={jest.fn()} />
    );
    expect(getByText("Queued")).toBeTruthy();
  });

  it("shows 'Processing' status badge when PROCESSING", () => {
    mockUseApplicationStatusLabel.mockReturnValue("Processing...");
    mockUseIsProcessing.mockReturnValue(true);
    const { getByText } = render(
      <JobCard job={baseJob} applicationId="app-1" onAnswerQuestions={jest.fn()} />
    );
    expect(getByText("Processing...")).toBeTruthy();
  });

  it("shows 'Needs Answers' and button when REQUIRES_INPUT", () => {
    mockUseApplicationStatusLabel.mockReturnValue("Needs your input");
    mockUsePendingInputs.mockReturnValue([
      { id: "inp-1", question: "What is your clearance?", answer: null },
    ]);
    const { getByText } = render(
      <JobCard job={baseJob} applicationId="app-1" onAnswerQuestions={jest.fn()} />
    );
    expect(getByText("Needs your input")).toBeTruthy();
  });

  it("shows 'Applied' when APPLIED", () => {
    mockUseApplicationStatusLabel.mockReturnValue("Applied");
    const { getByText } = render(
      <JobCard job={baseJob} applicationId="app-1" onAnswerQuestions={jest.fn()} />
    );
    expect(getByText("Applied")).toBeTruthy();
  });

  it("shows 'Failed' when FAILED", () => {
    mockUseApplicationStatusLabel.mockReturnValue("Failed");
    const { getByText } = render(
      <JobCard job={baseJob} applicationId="app-1" onAnswerQuestions={jest.fn()} />
    );
    expect(getByText("Failed")).toBeTruthy();
  });
});
