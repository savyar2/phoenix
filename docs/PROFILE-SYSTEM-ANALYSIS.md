# Profile System Analysis & Implementation Guide

## 🔄 Two Different Flows for Memory Creation

### Flow 1: Profile Answers → Memory Cards (Direct/Hardcoded)
**When:** User answers profile questions in the UI
**Method:** Direct conversion - NO Distiller
**Process:**
1. User answers a profile question
2. System directly creates a memory card based on question context
3. Hardcoded logic determines card type/domain from question text
4. Memory card saved immediately

**Example:**
- Question: "What are your dietary restrictions?"
- Answer: "I'm vegan"
- → Directly creates: `MemoryCard(type="constraint", text="User is vegan", domain=["eating", "dietary"])`

### Flow 2: Conversation Extraction → Memory Cards (LLM/Distiller)
**When:** User clicks "Extract" button on ChatGPT/Gemini conversation
**Method:** Use Distiller to extract semantic tuples
**Process:**
1. User clicks "Extract" on a conversation
2. System uses **Distiller** to extract semantic tuples from conversation text
3. Tuples are categorized into sub-profiles
4. Memory cards created from extracted tuples

**Example:**
- Conversation: "I need protein powder under $50 and have a coding deadline next week"
- → Distiller extracts: `(User HAS_GOAL Budget $50)`, `(User HAS_CONSTRAINT Coding Deadline)`
- → Creates memory cards from these tuples

**Key Point:** Profile answers use simple hardcoded conversion. Conversation extraction uses Distiller for intelligent extraction.

---

## ✅ What Actually Exists

### 1. **Distiller Service** (`router/app/services/distiller.py`) ✅ WORKING
- ✅ LLM-based extraction from text/conversations
- ✅ Supports OpenAI, Anthropic, Ollama with fallback
- ✅ Extracts semantic tuples (subject-predicate-object relationships)
- ✅ Can extract: PREFERS, HAS_GOAL, HAS_CONSTRAINT, LIKES, etc.
- ✅ Already integrated and working

### 2. **Memory Cards System** ✅ WORKING
- ✅ Memory card models (`MemoryCard` with type, domain, priority, text, tags, persona)
- ✅ Wallet store for encrypted storage
- ✅ API endpoints: `/api/memory-cards/create`, `/api/memory-cards/list`
- ✅ Can store constraints, preferences, goals, capabilities
- ✅ Domain-based categorization (food, shopping, coding, etc.)
- ✅ Persona support (Personal, Work, Travel)

### 3. **Profile Models** ⚠️ EXISTS BUT NOT FUNCTIONAL
- ⚠️ Files exist: `router/app/models/profile.py` and `router/app/api/routes/profile.py`
- ❌ **NOT registered in main.py** - routes are inaccessible
- ❌ **NOT tested** - may have bugs
- ⚠️ In-memory storage only (not persistent)
- ⚠️ Has structure for: UserProfile, SubProfile, ProfileQuestion, ProfileAnswer
- ⚠️ Has default questions defined but not accessible

### 4. **Extraction Service** ⚠️ EXISTS BUT BASIC
- ⚠️ File exists: `router/app/services/extraction_service.py`
- ⚠️ **Keyword-based only** - not using LLM
- ⚠️ Basic categorization logic
- ❌ **NOT connected to profile system**
- ❌ **NOT creating memory cards**

---

## ❌ What Needs to Be Built

### 1. **Profile System** (Build from scratch or fix existing)
- ❌ Register profile routes in `main.py`
- ❌ Test and fix profile API endpoints
- ❌ Add persistent storage (database)
- ❌ Create 12 main profile questions
- ❌ Create sub-profiles (Shopping, Eating, Health, Work)
- ❌ Add nested categories (Work → Finance, Coding, Projects, Meetings)

### 2. **Profile Answers → Memory Cards (Direct Conversion)**
- ❌ When user answers profile questions, directly create memory cards
- ❌ **NO Distiller needed** - simple hardcoded conversion
- ❌ Map question context to memory card type/domain
- ❌ Store answers as memory cards immediately

### 3. **Enhanced Extraction Service (Conversation → Memory)**
- ❌ **Use Distiller** for conversation extraction (ChatGPT/Gemini)
- ❌ Replace keyword-based with LLM-based extraction
- ❌ Categorize into sub-profiles automatically
- ❌ Create memory cards from extracted tuples

### 4. **Extraction API Endpoint**
- ❌ Create `POST /api/profile/{user_id}/extract` endpoint
- ❌ Accept conversation text from ChatGPT/Gemini
- ❌ **Use Distiller** to extract semantic tuples
- ❌ Convert tuples to memory cards
- ❌ Return categorized extractions

### 5. **Frontend Profile UI**
- ❌ Profile setup wizard (12 main questions)
- ❌ Sub-profile management UI
- ❌ Question/answer display and editing
- ❌ Integration with memory graph

### 6. **Chrome Extension "Extract" Button**
- ❌ Add button to ChatGPT/Claude/Gemini UI
- ❌ Capture conversation history
- ❌ Call extraction endpoint
- ❌ Show extraction results

---

## 📋 Step-by-Step Implementation Instructions

### Step 1: Build Profile Models (If fixing existing, skip to Step 2)

**File:** `router/app/models/profile.py`

Create models for:
- `ProfileQuestion` - Question structure
- `ProfileAnswer` - Answer structure  
- `SubProfile` - Sub-profile with categories
- `UserProfile` - Main profile with 12 questions + sub-profiles

**OR** verify existing file works and fix any issues.

---

### Step 2: Create Profile API Routes

**File:** `router/app/api/routes/profile.py`

Create endpoints:
- `POST /api/profile/create` - Create profile with 12 default questions
- `GET /api/profile/{user_id}` - Get user profile
- `POST /api/profile/{user_id}/answer` - Answer a question
- `POST /api/profile/{user_id}/sub-profile` - Create sub-profile
- `POST /api/profile/{user_id}/question` - Add question

**Default Questions (12 main):**
1. Primary occupation/field of work
2. Main hobbies/interests
3. Typical daily routine
4. Communication preferences
5. Dietary restrictions/preferences
6. Budget range for discretionary spending
7. Health and fitness goals
8. Learning preferences
9. Time management preferences
10. Technology comfort levels
11. Travel preferences
12. Long-term goals/aspirations

**Default Sub-Profiles:**
- **Shopping** (categories: Electronics, Clothing, Groceries, Books) - 5 questions
- **Eating** (categories: Restaurants, Cooking, Dietary, Cuisines) - 5 questions
- **Health** (categories: Fitness, Medical, Mental Health, Nutrition) - 5 questions
- **Work** (categories: Finance, Coding, Projects, Meetings) - 5 questions

---

### Step 3: Register Profile Routes

**File:** `router/app/main.py`

Add import:
```python
from app.api.routes import ingest, graph, memory_cards, agent, memverge, memmachine, profile
```

Add router:
```python
app.include_router(profile.router, prefix="/api/profile", tags=["Profile"])
```

**Test:**
```bash
curl http://127.0.0.1:8787/api/profile/demo_user
```

---

### Step 4: Add Profile Answer → Memory Card Conversion

**File:** `router/app/api/routes/profile.py`

In the `update_answer` endpoint, add direct memory card creation (NO Distiller):

```python
from wallet.store.wallet_store import WalletStore
from app.models.memory_card import MemoryCard

@router.post("/{user_id}/answer", response_model=ProfileResponse)
async def update_answer(user_id: str, request: UpdateAnswerRequest):
    """Answer a profile question and automatically create memory card."""
    try:
        profile = _profiles.get(user_id)
        if not profile:
            raise HTTPException(status_code=404, detail="Profile not found")
        
        # Find the question
        question = None
        for q in profile.main_questions:
            if q.id == request.question_id:
                question = q
                break
        
        if not question:
            # Check sub-profiles
            for sp in profile.sub_profiles:
                for q in sp.questions:
                    if q.id == request.question_id:
                        question = q
                        sub_profile = sp
                        break
        
        if not question:
            raise HTTPException(status_code=404, detail="Question not found")
        
        # Save answer to profile
        # ... (existing answer saving logic)
        
        # DIRECTLY CREATE MEMORY CARD (hardcoded, no Distiller)
        wallet = WalletStore(
            db_path=str(settings.get_wallet_path()),
            encryption_key=settings.wallet_encryption_key
        )
        
        # Determine memory card type from question context
        card_type = "preference"  # default
        if "restriction" in question.question_text.lower() or "constraint" in question.question_text.lower():
            card_type = "constraint"
        elif "goal" in question.question_text.lower() or "aspiration" in question.question_text.lower():
            card_type = "goal"
        
        # Determine domain from question/sub-profile context
        domain = []
        if hasattr(locals(), 'sub_profile'):
            domain.append(sub_profile.name.lower())
            # Add categories if available
            if sub_profile.categories:
                # Try to match question to category
                question_lower = question.question_text.lower()
                for cat in sub_profile.categories:
                    if cat.lower() in question_lower or any(kw in question_lower for kw in get_category_keywords(cat)):
                        domain.append(cat.lower())
        else:
            # Main profile question - infer domain from question text
            if "work" in question.question_text.lower() or "occupation" in question.question_text.lower():
                domain = ["work"]
            elif "food" in question.question_text.lower() or "diet" in question.question_text.lower():
                domain = ["eating", "food"]
            elif "health" in question.question_text.lower() or "fitness" in question.question_text.lower():
                domain = ["health"]
            elif "shopping" in question.question_text.lower() or "budget" in question.question_text.lower():
                domain = ["shopping"]
            else:
                domain = ["general"]
        
        # Create memory card directly from answer
        card = MemoryCard(
            type=card_type,
            text=f"User answered '{question.question_text}': {request.answer_text}",
            domain=domain,
            priority="soft",
            tags=[question.question_text[:50]] + (domain if domain else []),
            persona="Personal"
        )
        
        saved_card = wallet.add_card(card)
        logger.info(f"Created memory card {saved_card.id} from profile answer")
        
        return ProfileResponse(
            success=True,
            profile=profile,
            message=f"Answer saved and memory card created"
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

def get_category_keywords(category: str) -> List[str]:
    """Get keywords for matching questions to categories."""
    keywords = {
        "Finance": ["finance", "budget", "money", "cost", "expense", "financial"],
        "Coding": ["code", "programming", "language", "developer", "software"],
        "Projects": ["project", "task", "deadline", "deliverable"],
        "Meetings": ["meeting", "call", "schedule", "calendar"],
        "Restaurants": ["restaurant", "dining", "eat out"],
        "Cooking": ["cook", "recipe", "kitchen"],
        "Dietary": ["diet", "restriction", "allergy", "vegan", "vegetarian"],
        "Cuisines": ["cuisine", "food type", "ethnic"],
        "Fitness": ["fitness", "exercise", "workout", "gym"],
        "Medical": ["medical", "doctor", "health", "symptom"],
        "Mental Health": ["mental", "therapy", "stress", "anxiety"],
        "Nutrition": ["nutrition", "supplement", "vitamin", "diet"]
    }
    return keywords.get(category, [])
```

**Key Point:** Profile answers are converted directly to memory cards without using Distiller. This is hardcoded logic based on question context.

---

### Step 5: Enhance Extraction Service with LLM (For Conversations Only)

**File:** `router/app/services/extraction_service.py`

Replace keyword-based extraction with LLM-based using Distiller (ONLY for conversations, NOT for profile answers):

```python
from app.services.distiller import Distiller

@classmethod
async def extract_from_conversation(
    cls,
    conversation_text: str,
    messages: List[Dict],
    user_id: str
) -> Dict:
    """
    Extract relevant information from ChatGPT/Gemini conversations using LLM.
    
    NOTE: Profile answers use direct conversion (Step 4), NOT this service.
    This service is ONLY for conversation extraction.
    """
    try:
        # USE DISTILLER to extract semantic tuples from conversation
        tuples = await Distiller.extract_tuples(conversation_text, source="conversation")
        
        extracted_items = []
        categorized = {
            "Shopping": [],
            "Eating": [],
            "Health": [],
            "Work": {
                "Finance": [],
                "Coding": [],
                "Projects": [],
                "Meetings": []
            }
        }
        
        # Categorize tuples into sub-profiles
        for tuple_data in tuples:
            item = {
                "type": cls._tuple_to_card_type(tuple_data.predicate),
                "text": f"{tuple_data.subject} {tuple_data.predicate} {tuple_data.object}",
                "category": cls._categorize_tuple(tuple_data),
                "sub_category": cls._get_work_subcategory(tuple_data) if cls._categorize_tuple(tuple_data) == "Work" else None,
                "confidence": tuple_data.confidence,
                "properties": tuple_data.properties
            }
            
            extracted_items.append(item)
            
            # Add to categorized structure
            category = item["category"]
            if category == "Work" and item["sub_category"]:
                if item["sub_category"] in categorized["Work"]:
                    categorized["Work"][item["sub_category"]].append(item)
                else:
                    categorized["Work"]["Projects"].append(item)  # Default
            elif category in categorized:
                categorized[category].append(item)
        
        return {
            "extracted_items": extracted_items,
            "categorized": categorized
        }
    except Exception as e:
        logger.error(f"Extraction failed: {e}")
        # Fallback to keyword-based
        return cls._keyword_based_extraction(conversation_text)
    
@classmethod
def _tuple_to_card_type(cls, predicate: str) -> str:
    """Convert tuple predicate to memory card type."""
    if "CONSTRAINT" in predicate:
        return "constraint"
    elif "GOAL" in predicate:
        return "goal"
    elif "PREFERS" in predicate or "LIKES" in predicate:
        return "preference"
    else:
        return "preference"
    
@classmethod
def _categorize_tuple(cls, tuple_data) -> str:
    """Categorize tuple into sub-profile."""
    obj_type = tuple_data.object_type.lower()
    text = f"{tuple_data.object} {tuple_data.predicate}".lower()
    
    if any(kw in obj_type or kw in text for kw in ["shop", "purchase", "buy", "product", "shopping"]):
        return "Shopping"
    elif any(kw in obj_type or kw in text for kw in ["food", "restaurant", "meal", "dining", "diet", "eating", "cuisine"]):
        return "Eating"
    elif any(kw in obj_type or kw in text for kw in ["health", "fitness", "medical", "exercise", "wellness"]):
        return "Health"
    elif any(kw in obj_type or kw in text for kw in ["work", "project", "code", "finance", "meeting", "professional"]):
        return "Work"
    else:
        return "Shopping"  # Default
    
@classmethod
def _get_work_subcategory(cls, tuple_data) -> str:
    """Get work sub-category."""
    text = f"{tuple_data.object} {tuple_data.predicate}".lower()
    if any(kw in text for kw in ["finance", "budget", "money", "cost", "expense", "financial"]):
        return "Finance"
    elif any(kw in text for kw in ["code", "programming", "language", "function", "algorithm", "coding", "developer"]):
        return "Coding"
    elif any(kw in text for kw in ["meeting", "call", "schedule", "calendar", "appointment"]):
        return "Meetings"
    else:
        return "Projects"
    
@classmethod
def _keyword_based_extraction(cls, text: str) -> Dict:
    """Fallback keyword-based extraction."""
    # Keep existing keyword logic as fallback
    # ... (existing code)
```

---

### Step 6: Create Extraction API Endpoint (Conversation → Memory via Distiller)

**File:** `router/app/api/routes/profile.py`

Add at the end:
```python
from app.services.extraction_service import ExtractionService
from app.models.profile import ConversationExtractionRequest, ConversationExtractionResponse
from wallet.store.wallet_store import WalletStore
from app.models.memory_card import MemoryCard

@router.post("/{user_id}/extract", response_model=ConversationExtractionResponse)
async def extract_conversation(user_id: str, request: ConversationExtractionRequest):
    """
    Extract information from ChatGPT/Gemini conversation using Distiller.
    
    This endpoint:
    1. Uses Distiller to extract semantic tuples from conversation
    2. Categorizes tuples into sub-profiles
    3. Creates memory cards from extracted tuples
    
    NOTE: Profile answers are handled separately (direct conversion, no Distiller).
    """
    try:
        # STEP 1: Use Distiller to extract semantic tuples from conversation
        from app.services.distiller import Distiller
        
        tuples = await Distiller.extract_tuples(
            request.conversation_text, 
            source="conversation"
        )
        
        # STEP 2: Categorize tuples into sub-profiles
        result = await ExtractionService.extract_from_conversation(
            conversation_text=request.conversation_text,
            messages=request.messages,
            user_id=user_id
        )
        
        # STEP 3: Convert extracted tuples to memory cards
        wallet = WalletStore(
            db_path=str(settings.get_wallet_path()),
            encryption_key=settings.wallet_encryption_key
        )
        
        cards_created = []
        for item in result["extracted_items"]:
            # Determine domain from category
            domain = [item["category"].lower()]
            if item.get("sub_category"):
                domain.append(item["sub_category"].lower())
            
            card = MemoryCard(
                type=item.get("type", "preference"),
                text=item["text"],
                domain=domain,
                priority="soft",
                tags=[item["category"]] + ([item["sub_category"]] if item.get("sub_category") else []),
                persona="Personal"
            )
            wallet.add_card(card)
            cards_created.append(card.id)
        
        return ConversationExtractionResponse(
            success=True,
            extracted_items=result["extracted_items"],
            categorized=result["categorized"],
            message=f"Extracted {len(cards_created)} items and created {len(cards_created)} memory cards"
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
```

**Test:**
```bash
curl -X POST http://127.0.0.1:8787/api/profile/demo_user/extract \
  -H "Content-Type: application/json" \
  -d '{
    "conversation_id": "test_123",
    "conversation_text": "I need to buy protein powder under $50. Also, I have a coding project deadline next week.",
    "messages": [],
    "user_id": "demo_user"
  }'
```

---

### Step 7: Add Profile API to Frontend

**File:** `frontend/src/services/api.ts`

Add profile interfaces and API:

```typescript
export interface ProfileQuestion {
  id: string;
  question_text: string;
  question_type: 'text' | 'multiple_choice' | 'scale' | 'boolean';
  options?: string[];
  required: boolean;
  order: number;
}

export interface ProfileAnswer {
  question_id: string;
  answer_text: string;
  answer_data?: any;
  answered_at: string;
}

export interface SubProfile {
  id: string;
  name: string;
  description?: string;
  categories: string[];
  questions: ProfileQuestion[];
  answers: ProfileAnswer[];
}

export interface UserProfile {
  user_id: string;
  main_questions: ProfileQuestion[];
  main_answers: ProfileAnswer[];
  sub_profiles: SubProfile[];
}

export const profileApi = {
  get: (userId: string) => 
    api.get<{ success: boolean; profile: UserProfile }>(`/api/profile/${userId}`),
  
  create: (userId: string) => 
    api.post(`/api/profile/create`, { user_id: userId }),
  
  updateAnswer: (userId: string, questionId: string, answerText: string) =>
    api.post(`/api/profile/${userId}/answer`, { 
      question_id: questionId, 
      answer_text: answerText 
    }),
  
  createSubProfile: (userId: string, name: string, categories: string[]) =>
    api.post(`/api/profile/${userId}/sub-profile`, { name, categories }),
  
  extractConversation: (userId: string, conversationText: string, messages: any[]) =>
    api.post(`/api/profile/${userId}/extract`, {
      conversation_id: `conv_${Date.now()}`,
      conversation_text: conversationText,
      messages,
      user_id: userId
    }),
};
```

---

### Step 8: Create Profile UI Component

**File:** `frontend/src/components/ProfileManager.tsx`

Create component with:
- Main profile wizard (12 questions)
- Sub-profile sections
- Question/answer forms
- Category display

```typescript
import React, { useState, useEffect } from 'react';
import { profileApi, UserProfile, ProfileQuestion, ProfileAnswer } from '../services/api';

export default function ProfileManager() {
  const [profile, setProfile] = useState<UserProfile | null>(null);
  const [userId] = useState('demo_user');
  const [currentStep, setCurrentStep] = useState<'main' | 'sub' | 'view'>('main');
  const [answers, setAnswers] = useState<Record<string, string>>({});

  useEffect(() => {
    loadProfile();
  }, []);

  const loadProfile = async () => {
    try {
      const response = await profileApi.get(userId);
      if (response.data.success) {
        setProfile(response.data.profile);
        // Load existing answers into state
        const answerMap: Record<string, string> = {};
        response.data.profile.main_answers.forEach(a => {
          answerMap[a.question_id] = a.answer_text;
        });
        response.data.profile.sub_profiles.forEach(sp => {
          sp.answers.forEach(a => {
            answerMap[a.question_id] = a.answer_text;
          });
        });
        setAnswers(answerMap);
      }
    } catch (error) {
      console.error('Failed to load profile:', error);
    }
  };

  const handleAnswer = async (questionId: string, answerText: string) => {
    try {
      await profileApi.updateAnswer(userId, questionId, answerText);
      setAnswers({ ...answers, [questionId]: answerText });
    } catch (error) {
      console.error('Failed to save answer:', error);
    }
  };

  if (!profile) {
    return <div>Loading profile...</div>;
  }

  return (
    <div className="p-6 space-y-6 bg-gray-900 text-white min-h-screen">
      <h2 className="text-2xl font-bold">User Profile</h2>
      
      {/* Main Profile Questions */}
      {currentStep === 'main' && (
        <div>
          <h3 className="text-xl mb-4">Main Profile (12 Questions)</h3>
          {profile.main_questions
            .sort((a, b) => a.order - b.order)
            .map((q, idx) => (
            <div key={q.id} className="mb-4 p-4 bg-gray-800 rounded">
              <label className="block mb-2 font-semibold">
                {idx + 1}. {q.question_text}
              </label>
              {q.question_type === 'text' && (
                <input
                  type="text"
                  value={answers[q.id] || ''}
                  onChange={(e) => handleAnswer(q.id, e.target.value)}
                  className="w-full p-2 bg-gray-700 border border-gray-600 rounded text-white"
                  placeholder="Your answer..."
                />
              )}
              {q.question_type === 'multiple_choice' && q.options && (
                <select
                  value={answers[q.id] || ''}
                  onChange={(e) => handleAnswer(q.id, e.target.value)}
                  className="w-full p-2 bg-gray-700 border border-gray-600 rounded text-white"
                >
                  <option value="">Select an option...</option>
                  {q.options.map(opt => (
                    <option key={opt} value={opt}>{opt}</option>
                  ))}
                </select>
              )}
            </div>
          ))}
          <button 
            onClick={() => setCurrentStep('sub')} 
            className="mt-4 px-6 py-2 bg-blue-500 hover:bg-blue-600 text-white rounded"
          >
            Continue to Sub-Profiles →
          </button>
        </div>
      )}

      {/* Sub-Profiles */}
      {currentStep === 'sub' && (
        <div>
          <h3 className="text-xl mb-4">Sub-Profiles</h3>
          {profile.sub_profiles.map((sp) => (
            <div key={sp.id} className="mb-6 border border-gray-700 p-4 rounded bg-gray-800">
              <h4 className="font-bold text-lg mb-2">{sp.name}</h4>
              {sp.description && (
                <p className="text-sm text-gray-400 mb-2">{sp.description}</p>
              )}
              {sp.categories.length > 0 && (
                <div className="text-sm text-gray-400 mb-3">
                  <strong>Categories:</strong> {sp.categories.join(', ')}
                </div>
              )}
              <div className="space-y-3">
                {sp.questions
                  .sort((a, b) => a.order - b.order)
                  .map((q) => (
                  <div key={q.id}>
                    <label className="block mb-1 text-sm">{q.question_text}</label>
                    <input
                      type="text"
                      value={answers[q.id] || ''}
                      onChange={(e) => handleAnswer(q.id, e.target.value)}
                      className="w-full p-2 bg-gray-700 border border-gray-600 rounded text-white text-sm"
                      placeholder="Your answer..."
                    />
                  </div>
                ))}
              </div>
            </div>
          ))}
          <button 
            onClick={() => setCurrentStep('view')} 
            className="mt-4 px-6 py-2 bg-green-500 hover:bg-green-600 text-white rounded"
          >
            View Profile Summary
          </button>
        </div>
      )}

      {/* View Mode */}
      {currentStep === 'view' && (
        <div>
          <h3 className="text-xl mb-4">Profile Summary</h3>
          <div className="space-y-4">
            <div className="p-4 bg-gray-800 rounded">
              <h4 className="font-bold mb-2">Main Profile Answers</h4>
              {profile.main_questions.map(q => (
                <div key={q.id} className="mb-2">
                  <strong>{q.question_text}:</strong> {answers[q.id] || 'Not answered'}
                </div>
              ))}
            </div>
            {profile.sub_profiles.map(sp => (
              <div key={sp.id} className="p-4 bg-gray-800 rounded">
                <h4 className="font-bold mb-2">{sp.name}</h4>
                {sp.questions.map(q => (
                  <div key={q.id} className="mb-2 text-sm">
                    <strong>{q.question_text}:</strong> {answers[q.id] || 'Not answered'}
                  </div>
                ))}
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
```

---

### Step 9: Add Profile to Frontend App

**File:** `frontend/src/App.tsx`

Add ProfileManager as a new tab/panel:

```typescript
import ProfileManager from './components/ProfileManager';

// In your App component, add a tab or route for Profile
// For example, if using tabs:
const [activeTab, setActiveTab] = useState<'graph' | 'agent' | 'profile'>('graph');

// In render:
{activeTab === 'profile' && <ProfileManager />}
```

---

### Step 10: Add "Extract" Button to Chrome Extension

**File:** `extension/content.js`

Add extract button functionality:

```javascript
const ROUTER_URL = 'http://127.0.0.1:8787';

// Add extract button to chat interface
function addExtractButton() {
  const site = detectSite();
  if (!site) return;
  
  // Wait for page to fully load
  setTimeout(() => {
    const sendButton = findSendButton(site);
    if (!sendButton || document.querySelector('.phoenix-extract-btn')) return; // Already added
    
    // Create extract button
    const extractBtn = document.createElement('button');
    extractBtn.textContent = 'Extract';
    extractBtn.className = 'phoenix-extract-btn';
    extractBtn.style.cssText = 'margin-left: 10px; padding: 8px 16px; background: #4A90E2; color: white; border: none; border-radius: 4px; cursor: pointer; font-size: 14px;';
    
    extractBtn.addEventListener('click', async () => {
      extractBtn.disabled = true;
      extractBtn.textContent = 'Extracting...';
      
      try {
        const conversation = extractConversation(site);
        const response = await fetch(`${ROUTER_URL}/api/profile/demo_user/extract`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            conversation_id: `conv_${Date.now()}`,
            conversation_text: conversation.text,
            messages: conversation.messages,
            user_id: 'demo_user'
          })
        });
        
        const data = await response.json();
        if (data.success) {
          showExtractionResult(data);
        } else {
          alert('Extraction failed: ' + (data.message || 'Unknown error'));
        }
      } catch (error) {
        console.error('Extraction failed:', error);
        alert('Failed to extract conversation. Make sure the router is running.');
      } finally {
        extractBtn.disabled = false;
        extractBtn.textContent = 'Extract';
      }
    });
    
    // Insert button near send button
    if (sendButton.parentElement) {
      sendButton.parentElement.insertBefore(extractBtn, sendButton.nextSibling);
    }
  }, 2000);
}

function findSendButton(site) {
  if (site === 'chatgpt') {
    return document.querySelector('button[data-testid="send-button"]') ||
           document.querySelector('button[aria-label*="Send"]');
  }
  if (site === 'claude') {
    return document.querySelector('button[aria-label*="Send"]') ||
           document.querySelector('button:has(svg)');
  }
  if (site === 'gemini') {
    return document.querySelector('button[aria-label*="Send"]') ||
           document.querySelector('button.send-button');
  }
  return null;
}

function extractConversation(site) {
  const messages = [];
  let text = '';
  
  if (site === 'chatgpt') {
    // ChatGPT-specific: Extract all messages
    const messageElements = document.querySelectorAll('[data-message-author-role]');
    messageElements.forEach(el => {
      const role = el.getAttribute('data-message-author-role');
      const content = el.textContent || el.innerText;
      if (content && content.trim()) {
        messages.push({ role, content: content.trim() });
        text += `${role === 'user' ? 'User' : 'Assistant'}: ${content.trim()}\n\n`;
      }
    });
  } else if (site === 'claude') {
    // Claude-specific extraction
    const messageElements = document.querySelectorAll('[class*="message"]');
    messageElements.forEach(el => {
      const content = el.textContent || el.innerText;
      if (content && content.trim()) {
        messages.push({ role: 'user', content: content.trim() });
        text += `User: ${content.trim()}\n\n`;
      }
    });
  } else if (site === 'gemini') {
    // Gemini-specific extraction
    const messageElements = document.querySelectorAll('[data-message]');
    messageElements.forEach(el => {
      const content = el.textContent || el.innerText;
      if (content && content.trim()) {
        messages.push({ role: 'user', content: content.trim() });
        text += `User: ${content.trim()}\n\n`;
      }
    });
  }
  
  return { text: text.trim(), messages };
}

function showExtractionResult(data) {
  // Create modal to show results
  const modal = document.createElement('div');
  modal.className = 'phoenix-extract-modal';
  modal.style.cssText = 'position: fixed; top: 0; left: 0; right: 0; bottom: 0; background: rgba(0,0,0,0.7); z-index: 10000; display: flex; align-items: center; justify-content: center;';
  
  const categoriesHtml = Object.entries(data.categorized).map(([cat, items]) => {
    if (typeof items === 'object' && !Array.isArray(items)) {
      // Work sub-categories
      return `<div class="category-section">
        <strong>${cat}:</strong>
        ${Object.entries(items).map(([subCat, subItems]) => 
          `<div style="margin-left: 20px;">${subCat}: ${subItems.length} items</div>`
        ).join('')}
      </div>`;
    } else {
      return `<div><strong>${cat}:</strong> ${items.length} items</div>`;
    }
  }).join('');
  
  modal.innerHTML = `
    <div style="background: white; padding: 24px; border-radius: 8px; max-width: 500px; max-height: 80vh; overflow-y: auto;">
      <h3 style="margin-top: 0;">✅ Extraction Complete</h3>
      <p>Extracted <strong>${data.extracted_items.length}</strong> items</p>
      <div style="margin: 16px 0;">
        ${categoriesHtml}
      </div>
      <p style="color: #666; font-size: 12px;">${data.message || ''}</p>
      <button onclick="this.closest('.phoenix-extract-modal').remove()" 
              style="margin-top: 16px; padding: 8px 16px; background: #4A90E2; color: white; border: none; border-radius: 4px; cursor: pointer;">
        Close
      </button>
    </div>
  `;
  
  document.body.appendChild(modal);
  
  // Auto-close on outside click
  modal.addEventListener('click', (e) => {
    if (e.target === modal) {
      modal.remove();
    }
  });
}

// Initialize on page load
if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', addExtractButton);
} else {
  addExtractButton();
}

// Re-add button if page content changes (SPA navigation)
const observer = new MutationObserver(() => {
  if (!document.querySelector('.phoenix-extract-btn')) {
    addExtractButton();
  }
});
observer.observe(document.body, { childList: true, subtree: true });
```

---

### Step 11: Add Persistent Storage (Optional but Recommended)

**File:** `wallet/store/wallet_store.py` or create `profile_store.py`

Add methods to persist profiles to database instead of in-memory.

---

## 🧪 Testing Checklist

1. **Test Profile Creation:**
   ```bash
   curl -X POST http://127.0.0.1:8787/api/profile/create \
     -H "Content-Type: application/json" \
     -d '{"user_id": "demo_user"}'
   ```

2. **Test Get Profile:**
   ```bash
   curl http://127.0.0.1:8787/api/profile/demo_user
   ```

3. **Test Answer Question:**
   ```bash
   # First get profile to find a question_id
   curl http://127.0.0.1:8787/api/profile/demo_user | jq '.profile.main_questions[0].id'
   # Then answer it
   curl -X POST http://127.0.0.1:8787/api/profile/demo_user/answer \
     -H "Content-Type: application/json" \
     -d '{"question_id": "q_xxxxx", "answer_text": "Software Engineer"}'
   ```

4. **Test Extraction:**
   ```bash
   curl -X POST http://127.0.0.1:8787/api/profile/demo_user/extract \
     -H "Content-Type: application/json" \
     -d '{
       "conversation_id": "test",
       "conversation_text": "I need protein powder under $50 and have a coding deadline next week",
       "messages": [],
       "user_id": "demo_user"
     }'
   ```

5. **Verify Memory Cards Created:**
   ```bash
   curl http://127.0.0.1:8787/api/memory-cards/list?persona=Personal
   ```

---

## 📝 Summary

**What Actually Exists:**
- ✅ Distiller service (LLM extraction) - **WORKING**
- ✅ Memory cards system - **WORKING**
- ⚠️ Profile models/routes - **EXIST BUT NOT REGISTERED/ACCESSIBLE**
- ⚠️ Basic extraction service - **EXISTS BUT KEYWORD-BASED ONLY**

**What Needs to Be Built:**
1. Register profile routes (5 min)
2. Add profile answer → memory card conversion (direct, no Distiller) (20 min)
3. Enhance extraction service with Distiller (for conversations only) (30 min)
4. Create extraction endpoint (15 min)
5. Build frontend profile UI (2-3 hours)
6. Add Chrome extension extract button (1-2 hours)
7. Add persistent storage (1 hour)

**Total Estimated Time:** 4-6 hours

**Key Design Decision:**
- **Profile Answers** → Direct conversion to memory cards (hardcoded logic, NO Distiller)
- **Conversation Extraction** → Use Distiller to extract semantic tuples, then create memory cards

The foundation is there (Distiller + Memory Cards), you mainly need to:
- Wire up the profile system
- Add direct profile answer → memory card conversion
- Enhance conversation extraction to use Distiller
- Build the UI components
