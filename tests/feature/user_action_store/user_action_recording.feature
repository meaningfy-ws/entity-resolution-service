Feature: User action recording
  As a curation system
  I need to record curator actions against resolution decisions
  So that there is a traceable audit trail of all curation activity

  Background:
    Given a resolution decision exists for an entity mention
    And the decision has candidate clusters with confidence scores

  # --- Accept top candidate ---

  Scenario: Record an accept action for the top candidate
    Given the decision has not been curated on its current version
    When the curator accepts the top candidate
    Then a user action is recorded with action type "accept top"
    And the selected cluster matches the decision's current placement
    And the action captures all candidates as a snapshot

  Scenario: Accept action records the actor identity
    Given the decision has not been curated on its current version
    When the curator "curator@example.com" accepts the top candidate
    Then the recorded user action has actor "curator@example.com"

  # --- Reject all candidates ---

  Scenario: Record a reject action for all candidates
    Given the decision has not been curated on its current version
    When the curator rejects all candidates
    Then a user action is recorded with action type "reject all"
    And the selected cluster is empty
    And the action captures all candidates as a snapshot

  # --- Assign alternative candidate ---

  Scenario: Record an assign action for an alternative candidate
    Given the decision has not been curated on its current version
    And the decision has an alternative candidate "cluster-B"
    When the curator assigns the decision to cluster "cluster-B"
    Then a user action is recorded with action type "accept alternative"
    And the selected cluster is "cluster-B"

  Scenario: Assign to a cluster not in candidates is rejected
    Given the decision has not been curated on its current version
    When the curator assigns the decision to cluster "nonexistent-cluster"
    Then the action is rejected because the cluster is not a valid candidate
