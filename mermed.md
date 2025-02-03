erDiagram
Workspace ||--o{ Team : contains
Workspace ||--o{ WorkspaceMember : has

    Team ||--o{ TeamMember : has
    Team ||--o{ Task : owns

    User ||--o{ WorkspaceMember : belongs_to
    User ||--o{ TeamMember : joins
    User ||--o{ Task : creates

    Task ||--o{ TaskAssignment : has
    Task ||--o{ TimeEntry : tracks
    Task ||--o{ Comment : contains
    Task }|--|| Task : parent_of

    TaskAssignment }|--|| User : assigns_to
    TimeEntry }|--|| User : tracked_by
    Comment }|--|| User : written_by

erDiagram
%% Core Organizational Structure
Workspaces ||--o{ WorkspaceMembers : has
Workspaces ||--o{ Teams : contains
Workspaces {
UUID id PK
string name
string description
jsonb settings "Includes theme, features, limits"
string plan_type
string subscription_status
version int "Optimistic locking"
timestamp created_at
timestamp updated_at
}

    %% User Management
    Users ||--o{ WorkspaceMembers : belongs_to
    Users ||--o{ TeamMembers : joins
    Users ||--o{ Tasks : creates
    Users ||--o{ Sessions : has
    Users {
        UUID id PK
        string email UK
        string name
        string password_hash
        boolean is_active
        jsonb profile "Avatar, phone, timezone"
        jsonb preferences
        boolean two_factor_enabled
        timestamp last_login_at
        timestamp created_at
        timestamp updated_at
    }

    Sessions {
        UUID id PK
        UUID user_id FK
        string token_hash
        jsonb metadata "Device, IP, User-Agent"
        timestamp expires_at
        timestamp created_at
    }

    %% Team Organization
    Teams ||--o{ TeamMembers : has
    Teams ||--o{ Tasks : owns
    Teams {
        UUID id PK
        UUID workspace_id FK
        string name
        string description
        UUID owner_id FK
        jsonb settings
        boolean is_active
        timestamp created_at
        timestamp updated_at
    }

    TeamMembers {
        UUID id PK
        UUID team_id FK
        UUID user_id FK
        string role "admin|member|guest"
        jsonb permissions
        timestamp created_at
        timestamp updated_at
    }

    %% Task Management
    Tasks ||--o{ TaskAssignments : has
    Tasks ||--o{ Comments : contains
    Tasks ||--o{ TimeEntries : tracks
    Tasks }|--|| Tasks : parent_of
    Tasks {
        UUID id PK
        string title
        text description
        string status "backlog|todo|in_progress|review|done"
        string priority "low|medium|high|urgent"
        UUID parent_task_id FK
        UUID team_id FK
        UUID creator_id FK
        float estimated_hours
        float actual_hours
        jsonb metadata "Tags, custom fields"
        timestamp due_date
        timestamp completed_at
        version int "Optimistic locking"
        timestamp created_at
        timestamp updated_at
    }

    TaskAssignments {
        UUID id PK
        UUID task_id FK
        UUID user_id FK
        string role "owner|assignee|reviewer"
        timestamp created_at
    }

    TimeEntries {
        UUID id PK
        UUID task_id FK
        UUID user_id FK
        timestamp start_time
        timestamp end_time
        text description
        timestamp created_at
    }

    Comments {
        UUID id PK
        UUID task_id FK
        UUID user_id FK
        UUID parent_id FK "For threaded comments"
        text content
        jsonb attachments
        timestamp created_at
        timestamp updated_at
    }

    %% Unified Audit Trail
    AuditLog {
        UUID id PK
        string entity_type "workspace|user|team|task"
        UUID entity_id FK
        UUID actor_id FK "User who made the change"
        string action "create|update|delete"
        jsonb changes "Before/After states"
        jsonb metadata "IP, device info"
        timestamp created_at
    }

    %% Simplified Notifications
    Notifications {
        UUID id PK
        UUID user_id FK
        string type "task|mention|system"
        string title
        text content
        jsonb context "Related entities"
        boolean is_read
        timestamp created_at
        timestamp read_at
    }
