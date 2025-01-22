# Profile API

Manages Instagram user profiles for story checking. Handles profile creation, updates, and status management.

## Data Structure

```json
{
  "id": "string",
  "username": "string",
  "url": "string",
  "niche_id": "string",
  "status": "string",
  "active_story": boolean,
  "last_story_detected": "datetime",
  "total_checks": number,
  "total_detections": number,
  "detection_rate": number,
  "last_checked": "datetime",
  "last_detected": "datetime",
  "created_at": "datetime",
  "updated_at": "datetime"
}
```

## Status Values
- active: Profile is available for story checking
- suspended: Temporarily excluded from checks
- deleted: Soft deleted, can be reactivated

## Endpoints

### List Profiles
```http
GET /api/profiles
```

List profiles with optional filtering.

#### Query Parameters
- status: Filter by status (active, suspended, deleted)
- niche_id: Filter by niche
- has_story: Filter by active story status

#### Response
```json
[
  {
    "id": "string",
    "username": "string",
    "url": "string",
    "niche_id": "string",
    "status": "string",
    "active_story": boolean,
    "last_story_detected": "datetime",
    "total_checks": number,
    "total_detections": number,
    "detection_rate": number,
    "last_checked": "datetime",
    "last_detected": "datetime",
    "created_at": "datetime",
    "updated_at": "datetime"
  }
]
```

### Create Profile
```http
POST /api/profiles
```

Create a new profile.

#### Request Body
```json
{
  "username": "string",
  "url": "string" (optional),
  "niche_id": "string" (optional)
}
```

#### Response
```json
{
  "id": "string",
  ...profile data
}
```

#### Error Responses
- 400: Username is required
- 400: Username already exists
- 400: Invalid status value

### Import Profiles
```http
POST /api/profiles/niches/{niche_id}/import
```

Import profiles from a text file for a specific niche. Each line should contain either a username or Instagram profile URL.

#### Request Body
```
Content-Type: multipart/form-data

file: text file with usernames/URLs (one per line)
```

#### Response
```json
{
  "created": [Profile],
  "errors": [
    {
      "line": "string",
      "error": "string"
    }
  ]
}
```

Status Code:
- 201: All profiles created successfully
- 207: Partial success (some profiles created, some failed)
- 400: No file provided or invalid file
- 500: Server error

#### Error Types
- Invalid username format
- Profile already exists
- Server error

### Get Profile
```http
GET /api/profiles/{id}
```

Get a specific profile by ID.

#### Response
```json
{
  "id": "string",
  ...profile data
}
```

#### Error Responses
- 404: Profile not found

### Update Profile
```http
PUT /api/profiles/{id}
```

Update an existing profile.

#### Request Body
```json
{
  "username": "string" (optional),
  "url": "string" (optional),
  "niche_id": "string" (optional)
}
```

#### Error Responses
- 404: Profile not found
- 400: Username already exists

### Delete Profile
```http
DELETE /api/profiles/{id}
```

Soft delete a profile by setting status to 'deleted'.

#### Response
- 204: No Content
- 404: Profile not found

### Reactivate Profile
```http
POST /api/profiles/{id}/reactivate
```

Reactivate a soft-deleted profile by setting status to 'active'.

#### Response
```json
{
  "id": "string",
  ...profile data
}
```

#### Error Responses
- 404: Profile not found

## Implementation Details

### Model Features

1. Status Management
   - Simple status transitions (active/suspended/deleted)
   - Status affects batch inclusion
   - Soft delete via status field

2. Story Tracking
   - Current story status (active_story)
   - Last story detection time
   - Story check statistics

3. Niche Association
   - Optional niche assignment
   - Used for batch organization
   - Can be reassigned

### Usage Examples

#### Creating a Profile
```python
response = requests.post('/api/profiles', json={
    'username': 'example_user',
    'niche_id': 'fashion_niche_id'
})
```

#### File Import
```python
with open('profiles.txt', 'rb') as f:
    response = requests.post(
        '/api/profiles/niches/fashion_niche_id/import',
        files={'file': f}
    )
```

Example profiles.txt:
```
https://instagram.com/user1
user2
https://instagram.com/user3
```

#### Checking Story Status
```python
response = requests.get('/api/profiles', params={
    'has_story': True,
    'niche_id': 'fashion_niche_id'
})
```

### Best Practices

1. Profile Management
   - Use bulk creation for multiple profiles
   - Maintain unique usernames
   - Assign niches for organization

2. Status Handling
   - Use soft delete instead of hard delete
   - Suspend profiles temporarily if needed
   - Reactivate profiles when ready

3. Story Tracking
   - Monitor detection rates
   - Track story patterns
   - Use active_story flag for current state
