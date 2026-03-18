Feature: Decision curation actions
  As a curator
  I need to accept, reject, or reassign resolution decisions
  So that I can recommend corrections to entity clustering

  Background:
    Given the curator is authenticated and verified

  # --- Accept ---

  Scenario: Accept the top candidate for a decision
    Given a decision exists that has not been curated on its current version
    When the curator accepts the decision
    Then the system confirms the action with no content
    And a user action of type "accept top" is recorded

  Scenario: Accept a non-existent decision
    When the curator attempts to accept a decision that does not exist
    Then the system responds with a not found error

  Scenario: Accept a decision that was already curated
    Given a decision exists that has already been curated on its current version
    When the curator attempts to accept the decision
    Then the system responds with a conflict error indicating already curated

  # --- Reject ---

  Scenario: Reject all candidates for a decision
    Given a decision exists that has not been curated on its current version
    When the curator rejects the decision
    Then the system confirms the action with no content
    And a user action of type "reject all" is recorded

  Scenario: Reject a non-existent decision
    When the curator attempts to reject a decision that does not exist
    Then the system responds with a not found error

  # --- Assign ---

  Scenario: Assign a decision to an alternative cluster
    Given a decision exists with an alternative candidate "cluster-B"
    And the decision has not been curated on its current version
    When the curator assigns the decision to cluster "cluster-B"
    Then the system confirms the action with no content
    And a user action of type "accept alternative" is recorded for cluster "cluster-B"

  Scenario: Assign to a cluster not in candidates
    Given a decision exists that has not been curated on its current version
    When the curator assigns the decision to cluster "nonexistent-cluster"
    Then the system responds with a conflict error indicating an invalid cluster

  Scenario: Assign a non-existent decision
    When the curator attempts to assign a decision that does not exist to a cluster
    Then the system responds with a not found error