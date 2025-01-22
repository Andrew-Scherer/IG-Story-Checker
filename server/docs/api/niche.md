# Niche API

Handles categorization of Instagram profiles. Niches are used to organize profiles into groups and manage story checking targets.

## Data Structure

```json
{
  "id": "string",
  "name": "string",
  "display_order": number,
  "daily_story_target": number,
  "created_at": "datetime",
  "updated_at": "datetime"
}
```

## Endpoints

### List Niches
```http
GET /api/niches
```

Returns all niches in display order.

#### Response
```json
[
  {
    "id": "string",
    "name": "string",
    "display_order": number,
    "daily_story_target": number,
    "created_at": "datetime",
    "updated_at": "datetime"
  }
]
```

### Create Niche
```http
POST /api/niches
```

Create a new niche category.

#### Request Body
```json
{
  "name": "string",
  "display_order": number (optional),
  "daily_story_target": number (optional, default: 10)
}
```

#### Response
```json
{
  "id": "string",
  "name": "string",
  "display_order": number,
  "daily_story_target": number,
  "created_at": "datetime",
  "updated_at": "datetime"
}
```

#### Error Responses
- 400: Name is required
- 400: Name already exists
- 400: Name cannot be empty

### Get Niche
```http
GET /api/niches/{id}
```

Get a specific niche by ID.

#### Response
```json
{
  "id": "string",
  "name": "string",
  "display_order": number,
  "daily_story_target": number,
  "created_at": "datetime",
  "updated_at": "datetime"
}
```

#### Error Responses
- 404: Niche not found

### Update Niche
```http
PUT /api/niches/{id}
```

Update an existing niche.

#### Request Body
```json
{
  "name": "string" (optional),
  "display_order": number (optional),
  "daily_story_target": number (optional)
}
```

#### Response
```json
{
  "id": "string",
  "name": "string",
  "display_order": number,
  "daily_story_target": number,
  "created_at": "datetime",
  "updated_at": "datetime"
}
```

#### Error Responses
- 404: Niche not found
- 400: Name already exists
- 400: Name cannot be empty

### Delete Niche
```http
DELETE /api/niches/{id}
```

Delete a niche. Note: This will not delete associated profiles.

#### Response
- 204: No Content on success
- 404: Niche not found

### Reorder Niches
```http
POST /api/niches/reorder
```

Update display order of niches.

#### Request Body
```json
{
  "niche_ids": ["string"]
}
```

#### Response
```json
{
  "message": "Niches reordered successfully"
}
```

#### Error Responses
- 400: Invalid niche ID
- 400: All niches must be included

## Implementation Notes

### Model Details
The Niche model includes:
- UUID primary key
- Unique name constraint
- Display order for UI sorting
- Daily story target for batch processing
- Standard timestamps (created_at, updated_at)

### Key Features
1. Display Order Management
   - Niches maintain a display order for consistent UI presentation
   - Reorder endpoint handles bulk updates to display order
   - New niches default to end of order

2. Story Target Tracking
   - Each niche has a daily story target
   - Used by batch processing to determine when to trigger new checks
   - Configurable per niche for different monitoring intensities

3. Profile Association
   - One-to-many relationship with profiles
   - Deleting a niche does not delete associated profiles
   - Profiles can be reassigned to different niches

### Usage Examples

#### Creating a Niche
```python
response = requests.post('/api/niches', json={
    'name': 'Fashion',
    'daily_story_target': 20
})
```

#### Updating Display Order
```python
response = requests.post('/api/niches/reorder', json={
    'niche_ids': ['id1', 'id2', 'id3']
})
```

#### Filtering Active Profiles by Niche
```python
response = requests.get('/api/profiles', params={
    'niche_id': 'niche_id',
    'status': 'active'
})
