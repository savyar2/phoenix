# Manual Memory Card Creation

When LLM providers are unavailable, you can create Memory Cards manually.

## API Endpoints

### Create Memory Card

**POST** `/api/memory-cards/create`

**Content-Type:** `application/json`

**Request Body:**
```json
{
  "type": "constraint",
  "text": "I'm vegan",
  "domain": ["food", "dining"],
  "priority": "hard",
  "tags": ["diet", "restrictions"],
  "persona": "Personal"
}
```

**Response:**
```json
{
  "success": true,
  "card": {
    "id": "card_abc123",
    "type": "constraint",
    "text": "I'm vegan",
    "domain": ["food", "dining"],
    "priority": "hard",
    "tags": ["diet", "restrictions"],
    "persona": "Personal",
    "created_at": "2024-01-01T12:00:00",
    "updated_at": null
  },
  "message": "Memory card 'card_abc123' created successfully"
}
```

### List Memory Cards

**GET** `/api/memory-cards/list?persona=Personal&domain=food`

**Query Parameters:**
- `persona` (optional, default: "Personal"): Filter by persona
- `domain` (optional): Filter by domain

**Response:**
```json
{
  "success": true,
  "cards": [...],
  "count": 5
}
```

### Get Specific Card

**GET** `/api/memory-cards/{card_id}`

**Response:**
```json
{
  "success": true,
  "card": {
    "id": "card_abc123",
    ...
  }
}
```

### Delete Card

**DELETE** `/api/memory-cards/{card_id}`

**Response:**
```json
{
  "success": true,
  "message": "Memory card 'card_abc123' deleted successfully"
}
```

## Example: Creating a Budget Constraint

```bash
curl -X POST http://localhost:8787/api/memory-cards/create \
  -H "Content-Type: application/json" \
  -d '{
    "type": "constraint",
    "text": "Monthly budget limit: $50 for supplements",
    "domain": ["shopping", "health"],
    "priority": "hard",
    "tags": ["budget", "supplements"],
    "persona": "Personal"
  }'
```

## Memory Card Types

- **constraint**: Hard limitations (e.g., "I'm vegan", "Budget limit: $50")
- **preference**: Soft preferences (e.g., "I like Italian food")
- **goal**: Objectives (e.g., "Lose 10 pounds by March")
- **capability**: Skills/abilities (e.g., "I can code in Python")

## Priority Levels

- **hard**: Overrides preferences (e.g., dietary restrictions, budget limits)
- **soft**: Can be overridden by hard constraints (e.g., food preferences)

## Use Cases

1. **Privacy Mode**: Create cards manually when you don't want to use cloud LLMs
2. **LLM Unavailable**: When all LLM providers are down or unavailable
3. **Precise Control**: When you want exact wording without LLM interpretation
4. **Bulk Import**: Programmatically create many cards from existing data

