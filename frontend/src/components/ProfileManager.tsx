import React, { useState, useEffect } from 'react';
import { profileApi, UserProfile, ProfileQuestion, ProfileAnswer } from '../services/api';

export default function ProfileManager() {
  const [profile, setProfile] = useState<UserProfile | null>(null);
  const [userId] = useState('demo_user');
  const [currentStep, setCurrentStep] = useState<'main' | 'sub' | 'view'>('main');
  const [answers, setAnswers] = useState<Record<string, string>>({});
  const [pendingAnswers, setPendingAnswers] = useState<Record<string, string>>({});
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [successMessage, setSuccessMessage] = useState<string | null>(null);

  useEffect(() => {
    loadProfile();
  }, []);

  const loadProfile = async () => {
    try {
      setLoading(true);
      const response = await profileApi.get(userId);
      if (response.data.success) {
        setProfile(response.data.profile);
        // Load existing answers into state
        const answerMap: Record<string, string> = {};
        response.data.profile.main_answers.forEach((a: ProfileAnswer) => {
          answerMap[a.question_id] = a.answer_text;
        });
        response.data.profile.sub_profiles.forEach((sp: any) => {
          sp.answers.forEach((a: ProfileAnswer) => {
            answerMap[a.question_id] = a.answer_text;
          });
        });
        setAnswers(answerMap);
        setPendingAnswers(answerMap);
      }
    } catch (error: any) {
      console.error('Failed to load profile:', error);
      setError(error.response?.data?.detail || 'Failed to load profile');
    } finally {
      setLoading(false);
    }
  };

  const handleSelectOption = (questionId: string, value: string) => {
    setPendingAnswers({ ...pendingAnswers, [questionId]: value });
  };

  const handleSaveAll = async () => {
    setSaving(true);
    setError(null);
    setSuccessMessage(null);
    
    try {
      // Find all changed answers
      const changedQuestionIds = Object.keys(pendingAnswers).filter(
        qId => pendingAnswers[qId] !== answers[qId] && pendingAnswers[qId]
      );
      
      // Save each changed answer
      for (const questionId of changedQuestionIds) {
        await profileApi.updateAnswer(userId, questionId, pendingAnswers[questionId]);
      }
      
      setAnswers({ ...pendingAnswers });
      setSuccessMessage(`Saved ${changedQuestionIds.length} answer(s) successfully!`);
      setTimeout(() => setSuccessMessage(null), 3000);
    } catch (error: any) {
      console.error('Failed to save answers:', error);
      setError(error.response?.data?.detail || 'Failed to save answers');
    } finally {
      setSaving(false);
    }
  };

  const handleClearAll = () => {
    // Clear pending answers for current view
    if (currentStep === 'main' && profile) {
      const cleared: Record<string, string> = { ...pendingAnswers };
      profile.main_questions.forEach(q => {
        cleared[q.id] = '';
      });
      setPendingAnswers(cleared);
    } else if (currentStep === 'sub' && profile) {
      const cleared: Record<string, string> = { ...pendingAnswers };
      profile.sub_profiles.forEach(sp => {
        sp.questions.forEach(q => {
          cleared[q.id] = '';
        });
      });
      setPendingAnswers(cleared);
    }
  };

  const hasUnsavedChanges = () => {
    return Object.keys(pendingAnswers).some(
      qId => pendingAnswers[qId] !== answers[qId]
    );
  };

  // Radio button choice component
  const RadioChoices = ({ question, selectedValue, onChange }: {
    question: ProfileQuestion;
    selectedValue: string;
    onChange: (value: string) => void;
  }) => {
    if (!question.options) return null;
    
    return (
      <div className="flex flex-wrap gap-3 mt-2">
        {question.options.map(opt => (
          <label
            key={opt}
            className={`
              flex items-center gap-2 px-4 py-3 rounded-lg border-2 cursor-pointer transition-all
              ${selectedValue === opt 
                ? 'border-blue-500 bg-blue-500/10 text-white' 
                : 'border-gray-600 bg-gray-800 text-gray-300 hover:border-gray-500'
              }
            `}
          >
            <input
              type="radio"
              name={question.id}
              value={opt}
              checked={selectedValue === opt}
              onChange={() => onChange(opt)}
              className="w-4 h-4 text-blue-500 bg-gray-700 border-gray-600 focus:ring-blue-500"
            />
            <span className="text-sm font-medium">{opt}</span>
          </label>
        ))}
      </div>
    );
  };

  if (loading) {
    return (
      <div className="p-6 bg-gray-900 text-white min-h-screen flex items-center justify-center">
        <div>Loading profile...</div>
      </div>
    );
  }

  if (error && !profile) {
    return (
      <div className="p-6 bg-gray-900 text-white min-h-screen flex items-center justify-center">
        <div className="text-red-400">Error: {error}</div>
      </div>
    );
  }

  if (!profile) {
    return (
      <div className="p-6 bg-gray-900 text-white min-h-screen flex items-center justify-center">
        <button
          onClick={async () => {
            try {
              await profileApi.create(userId);
              await loadProfile();
            } catch (error: any) {
              setError(error.response?.data?.detail || 'Failed to create profile');
            }
          }}
          className="px-6 py-2 bg-blue-500 hover:bg-blue-600 text-white rounded"
        >
          Create Profile
        </button>
      </div>
    );
  }

  return (
    <div className="p-6 space-y-6 bg-gray-900 text-white min-h-screen">
      <div className="flex justify-between items-center">
        <h2 className="text-2xl font-bold">User Profile</h2>
        <div className="flex gap-2">
          <button
            onClick={() => setCurrentStep('main')}
            className={`px-4 py-2 rounded ${currentStep === 'main' ? 'bg-blue-500' : 'bg-gray-700'}`}
          >
            Main Profile
          </button>
          <button
            onClick={() => setCurrentStep('sub')}
            className={`px-4 py-2 rounded ${currentStep === 'sub' ? 'bg-blue-500' : 'bg-gray-700'}`}
          >
            Sub-Profiles
          </button>
          <button
            onClick={() => setCurrentStep('view')}
            className={`px-4 py-2 rounded ${currentStep === 'view' ? 'bg-blue-500' : 'bg-gray-700'}`}
          >
            View Summary
          </button>
        </div>
      </div>

      {error && (
        <div className="p-4 bg-red-900 text-red-200 rounded">
          {error}
        </div>
      )}

      {successMessage && (
        <div className="p-4 bg-green-900 text-green-200 rounded">
          {successMessage}
        </div>
      )}

      {/* Main Profile Questions */}
      {currentStep === 'main' && (
        <div>
          <h3 className="text-xl mb-4">Main Profile Questions</h3>
          {profile.main_questions.length === 0 ? (
            <div className="p-4 bg-gray-800 rounded">
              <p className="text-gray-400">No main profile questions yet. Add questions to get started.</p>
            </div>
          ) : (
            <div className="space-y-6">
              {profile.main_questions
                .sort((a, b) => a.order - b.order)
                .map((q, idx) => (
                  <div key={q.id} className="p-5 bg-gray-800 rounded-lg">
                    <label className="block text-lg font-medium mb-1">
                      {idx + 1}. {q.question_text}
                    </label>
                    {q.question_type === 'text' && (
                      <input
                        type="text"
                        value={pendingAnswers[q.id] || ''}
                        onChange={(e) => handleSelectOption(q.id, e.target.value)}
                        className="w-full p-2 bg-gray-700 border border-gray-600 rounded text-white mt-2"
                        placeholder="Your answer..."
                      />
                    )}
                    {q.question_type === 'multiple_choice' && q.options && (
                      <RadioChoices
                        question={q}
                        selectedValue={pendingAnswers[q.id] || ''}
                        onChange={(value) => handleSelectOption(q.id, value)}
                      />
                    )}
                  </div>
                ))}
            </div>
          )}
          
          {/* Save and Clear buttons */}
          {profile.main_questions.length > 0 && (
            <div className="flex gap-4 mt-8 pt-6 border-t border-gray-700">
              <button
                onClick={handleSaveAll}
                disabled={saving || !hasUnsavedChanges()}
                className={`
                  px-8 py-3 rounded-lg font-semibold text-white transition-all
                  ${saving || !hasUnsavedChanges()
                    ? 'bg-gray-600 cursor-not-allowed'
                    : 'bg-green-600 hover:bg-green-700'
                  }
                `}
              >
                {saving ? 'Saving...' : 'Save Answers'}
              </button>
              <button
                onClick={handleClearAll}
                className="px-8 py-3 rounded-lg font-semibold text-white bg-gray-700 hover:bg-gray-600 transition-all"
              >
                Clear Choices
              </button>
              {hasUnsavedChanges() && (
                <span className="flex items-center text-yellow-400 text-sm">
                  ● Unsaved changes
                </span>
              )}
            </div>
          )}
        </div>
      )}

      {/* Sub-Profiles */}
      {currentStep === 'sub' && (
        <div>
          <h3 className="text-xl mb-4">Sub-Profiles</h3>
          {profile.sub_profiles.map((sp) => (
            <div key={sp.id} className="mb-8 border border-gray-700 p-5 rounded-lg bg-gray-800">
              <h4 className="font-bold text-xl mb-2">{sp.name}</h4>
              {sp.description && (
                <p className="text-sm text-gray-400 mb-3">{sp.description}</p>
              )}
              {sp.categories.length > 0 && (
                <div className="text-sm text-gray-400 mb-4">
                  <strong>Categories:</strong> {sp.categories.join(', ')}
                </div>
              )}
              {sp.questions.length === 0 ? (
                <p className="text-gray-400 text-sm">No questions yet for this sub-profile.</p>
              ) : (
                <div className="space-y-5">
                  {sp.questions
                    .sort((a, b) => a.order - b.order)
                    .map((q, idx) => (
                      <div key={q.id} className="p-4 bg-gray-750 rounded-lg border border-gray-700">
                        <label className="block text-base font-medium mb-1">
                          {idx + 1}. {q.question_text}
                        </label>
                        {q.question_type === 'text' && (
                          <input
                            type="text"
                            value={pendingAnswers[q.id] || ''}
                            onChange={(e) => handleSelectOption(q.id, e.target.value)}
                            className="w-full p-2 bg-gray-700 border border-gray-600 rounded text-white text-sm mt-2"
                            placeholder="Your answer..."
                          />
                        )}
                        {q.question_type === 'multiple_choice' && q.options && (
                          <RadioChoices
                            question={q}
                            selectedValue={pendingAnswers[q.id] || ''}
                            onChange={(value) => handleSelectOption(q.id, value)}
                          />
                        )}
                      </div>
                    ))}
                </div>
              )}
            </div>
          ))}
          
          {/* Save and Clear buttons for sub-profiles */}
          {profile.sub_profiles.some(sp => sp.questions.length > 0) && (
            <div className="flex gap-4 mt-8 pt-6 border-t border-gray-700">
              <button
                onClick={handleSaveAll}
                disabled={saving || !hasUnsavedChanges()}
                className={`
                  px-8 py-3 rounded-lg font-semibold text-white transition-all
                  ${saving || !hasUnsavedChanges()
                    ? 'bg-gray-600 cursor-not-allowed'
                    : 'bg-green-600 hover:bg-green-700'
                  }
                `}
              >
                {saving ? 'Saving...' : 'Save Answers'}
              </button>
              <button
                onClick={handleClearAll}
                className="px-8 py-3 rounded-lg font-semibold text-white bg-gray-700 hover:bg-gray-600 transition-all"
              >
                Clear Choices
              </button>
              {hasUnsavedChanges() && (
                <span className="flex items-center text-yellow-400 text-sm">
                  ● Unsaved changes
                </span>
              )}
            </div>
          )}
        </div>
      )}

      {/* View Mode */}
      {currentStep === 'view' && (
        <div>
          <h3 className="text-xl mb-4">Profile Summary</h3>
          <div className="space-y-4">
            <div className="p-4 bg-gray-800 rounded">
              <h4 className="font-bold mb-2">Main Profile Answers</h4>
              {profile.main_questions.length === 0 ? (
                <p className="text-gray-400">No main profile questions yet.</p>
              ) : (
                profile.main_questions.map(q => (
                  <div key={q.id} className="mb-2">
                    <strong>{q.question_text}:</strong>{' '}
                    <span className={answers[q.id] ? 'text-green-400' : 'text-gray-500'}>
                      {answers[q.id] || 'Not answered'}
                    </span>
                  </div>
                ))
              )}
            </div>
            {profile.sub_profiles.map(sp => (
              <div key={sp.id} className="p-4 bg-gray-800 rounded">
                <h4 className="font-bold mb-2">{sp.name}</h4>
                {sp.questions.length === 0 ? (
                  <p className="text-gray-400 text-sm">No questions yet.</p>
                ) : (
                  sp.questions.map(q => (
                    <div key={q.id} className="mb-2 text-sm">
                      <strong>{q.question_text}:</strong>{' '}
                      <span className={answers[q.id] ? 'text-green-400' : 'text-gray-500'}>
                        {answers[q.id] || 'Not answered'}
                      </span>
                    </div>
                  ))
                )}
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
