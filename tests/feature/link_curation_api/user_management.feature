Feature: User management
  As an administrator
  I need to create, list, update, and remove user accounts
  So that I can control who has access to curation functionality

  Background:
    Given the administrator is authenticated

  # --- Create user ---

  Scenario: Create a new user
    When the administrator creates a user with email "newcurator@example.com"
    Then the user account is created
    And the response contains the user details without the password

  Scenario: Create a user with a duplicate email
    Given a user exists with email "existing@example.com"
    When the administrator creates a user with email "existing@example.com"
    Then the creation is rejected because the email is already in use

  # --- List users ---

  Scenario: List all users with pagination
    Given 15 user accounts exist
    When the administrator requests the user list with 10 items per page
    Then 10 users are returned
    And the total count is 15

  # --- Update user ---

  Scenario Outline: Update user flags
    Given a user account exists
    When the administrator sets the user's "<flag>" to <value>
    Then the user record reflects the updated flag

    Examples:
      | flag          | value |
      | active        | false |
      | superuser     | true  |
      | verified      | true  |

  Scenario: Update a non-existent user
    When the administrator attempts to update a user that does not exist
    Then the system responds with a not found error

  # --- Delete user ---

  Scenario: Delete a user
    Given a user account exists
    When the administrator deletes the user
    Then the user is removed from the system

  Scenario: Delete a non-existent user
    When the administrator attempts to delete a user that does not exist
    Then the system responds with a not found error

  # --- Current user ---

  Scenario: View current authenticated user
    When an authenticated user requests their own profile
    Then the response contains the user's email and role flags