import React, { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Plus, Trash2, Save, X, Tag, Hash } from 'lucide-react';
import { memoryCardsApi, MemoryCard, CreateMemoryCardRequest } from '../services/api';

interface MemoryCardManagerProps {
  onCardCreated?: () => void;
}

const MemoryCardManager: React.FC<MemoryCardManagerProps> = ({ onCardCreated }) => {
  const [cards, setCards] = useState<MemoryCard[]>([]);
  const [loading, setLoading] = useState(false);
  const [showForm, setShowForm] = useState(false);
  const [selectedPersona, setSelectedPersona] = useState('Personal');
  const [formData, setFormData] = useState<CreateMemoryCardRequest>({
    type: 'preference',
    text: '',
    domain: [],
    priority: 'soft',
    tags: [],
    persona: 'Personal',
  });
  const [domainInput, setDomainInput] = useState('');
  const [tagInput, setTagInput] = useState('');

  const personas = ['Personal', 'Work', 'Travel'];
  const cardTypes = ['constraint', 'preference', 'goal', 'capability'] as const;

  // Fetch cards
  const fetchCards = async () => {
    try {
      setLoading(true);
      const response = await memoryCardsApi.list(selectedPersona);
      setCards(response.data.cards || []);
    } catch (error) {
      console.error('Failed to fetch memory cards:', error);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchCards();
  }, [selectedPersona]);

  // Create card
  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      setLoading(true);
      await memoryCardsApi.create(formData);
      setShowForm(false);
      resetForm();
      await fetchCards();
      onCardCreated?.();
    } catch (error) {
      console.error('Failed to create memory card:', error);
      alert('Failed to create memory card. Check console for details.');
    } finally {
      setLoading(false);
    }
  };

  // Delete card
  const handleDelete = async (cardId: string) => {
    if (!confirm('Are you sure you want to delete this memory card?')) return;
    
    try {
      await memoryCardsApi.delete(cardId);
      await fetchCards();
    } catch (error) {
      console.error('Failed to delete memory card:', error);
    }
  };

  const resetForm = () => {
    setFormData({
      type: 'preference',
      text: '',
      domain: [],
      priority: 'soft',
      tags: [],
      persona: 'Personal',
    });
    setDomainInput('');
    setTagInput('');
  };

  const addDomain = () => {
    if (domainInput.trim() && !formData.domain.includes(domainInput.trim())) {
      setFormData({
        ...formData,
        domain: [...formData.domain, domainInput.trim()],
      });
      setDomainInput('');
    }
  };

  const removeDomain = (domain: string) => {
    setFormData({
      ...formData,
      domain: formData.domain.filter(d => d !== domain),
    });
  };

  const addTag = () => {
    if (tagInput.trim() && !formData.tags.includes(tagInput.trim())) {
      setFormData({
        ...formData,
        tags: [...formData.tags, tagInput.trim()],
      });
      setTagInput('');
    }
  };

  const removeTag = (tag: string) => {
    setFormData({
      ...formData,
      tags: formData.tags.filter(t => t !== tag),
    });
  };

  const getTypeColor = (type: string) => {
    switch (type) {
      case 'constraint':
        return 'bg-red-500/20 text-red-400 border-red-500/30';
      case 'preference':
        return 'bg-green-500/20 text-green-400 border-green-500/30';
      case 'goal':
        return 'bg-blue-500/20 text-blue-400 border-blue-500/30';
      case 'capability':
        return 'bg-purple-500/20 text-purple-400 border-purple-500/30';
      default:
        return 'bg-white/10 text-white/60 border-white/20';
    }
  };

  const getPriorityBadge = (priority: string) => {
    return priority === 'hard' ? (
      <span className="px-2 py-0.5 text-xs rounded-full bg-red-500/20 text-red-400 border border-red-500/30">
        Hard
      </span>
    ) : (
      <span className="px-2 py-0.5 text-xs rounded-full bg-yellow-500/20 text-yellow-400 border border-yellow-500/30">
        Soft
      </span>
    );
  };

  return (
    <motion.div
      className="glass-panel p-6"
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.5 }}
    >
      <div className="flex justify-between items-center mb-6">
        <h2 className="text-lg font-semibold flex items-center gap-2">
          <span className="text-2xl">💾</span>
          Memory Cards
        </h2>
        <div className="flex items-center gap-3">
          <select
            value={selectedPersona}
            onChange={(e) => setSelectedPersona(e.target.value)}
            className="bg-white/5 border border-white/10 rounded-lg px-3 py-1.5 text-sm focus:outline-none focus:border-phoenix-500/50"
          >
            {personas.map(p => (
              <option key={p} value={p}>{p}</option>
            ))}
          </select>
          <motion.button
            whileHover={{ scale: 1.05 }}
            whileTap={{ scale: 0.95 }}
            onClick={() => setShowForm(!showForm)}
            className="flex items-center gap-2 px-4 py-2 bg-phoenix-500 hover:bg-phoenix-600 rounded-lg font-medium transition-colors"
          >
            <Plus size={18} />
            Add Card
          </motion.button>
        </div>
      </div>

      {/* Create Form */}
      <AnimatePresence>
        {showForm && (
          <motion.div
            initial={{ opacity: 0, height: 0 }}
            animate={{ opacity: 1, height: 'auto' }}
            exit={{ opacity: 0, height: 0 }}
            className="mb-6 p-4 bg-white/5 rounded-xl border border-white/10"
          >
            <form onSubmit={handleSubmit} className="space-y-4">
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-xs text-white/50 uppercase tracking-wider mb-2">
                    Type
                  </label>
                  <select
                    value={formData.type}
                    onChange={(e) => setFormData({ ...formData, type: e.target.value as any })}
                    className="w-full bg-white/5 border border-white/10 rounded-lg px-3 py-2 text-sm focus:outline-none focus:border-phoenix-500/50"
                  >
                    {cardTypes.map(type => (
                      <option key={type} value={type}>{type}</option>
                    ))}
                  </select>
                </div>
                <div>
                  <label className="block text-xs text-white/50 uppercase tracking-wider mb-2">
                    Priority
                  </label>
                  <select
                    value={formData.priority}
                    onChange={(e) => setFormData({ ...formData, priority: e.target.value as 'hard' | 'soft' })}
                    className="w-full bg-white/5 border border-white/10 rounded-lg px-3 py-2 text-sm focus:outline-none focus:border-phoenix-500/50"
                  >
                    <option value="soft">Soft</option>
                    <option value="hard">Hard</option>
                  </select>
                </div>
              </div>

              <div>
                <label className="block text-xs text-white/50 uppercase tracking-wider mb-2">
                  Text
                </label>
                <textarea
                  value={formData.text}
                  onChange={(e) => setFormData({ ...formData, text: e.target.value })}
                  placeholder="Enter the constraint, preference, goal, or capability..."
                  required
                  rows={3}
                  className="w-full bg-white/5 border border-white/10 rounded-lg px-3 py-2 text-sm placeholder:text-white/30 focus:outline-none focus:border-phoenix-500/50"
                />
              </div>

              <div>
                <label className="block text-xs text-white/50 uppercase tracking-wider mb-2">
                  Domains
                </label>
                <div className="flex gap-2 mb-2">
                  <input
                    type="text"
                    value={domainInput}
                    onChange={(e) => setDomainInput(e.target.value)}
                    onKeyPress={(e) => e.key === 'Enter' && (e.preventDefault(), addDomain())}
                    placeholder="e.g., food, shopping, coding"
                    className="flex-1 bg-white/5 border border-white/10 rounded-lg px-3 py-2 text-sm placeholder:text-white/30 focus:outline-none focus:border-phoenix-500/50"
                  />
                  <button
                    type="button"
                    onClick={addDomain}
                    className="px-3 py-2 bg-white/10 hover:bg-white/20 rounded-lg transition-colors"
                  >
                    <Plus size={16} />
                  </button>
                </div>
                <div className="flex flex-wrap gap-2">
                  {formData.domain.map(domain => (
                    <span
                      key={domain}
                      className="flex items-center gap-1 px-2 py-1 bg-phoenix-500/20 text-phoenix-400 rounded-lg text-xs"
                    >
                      <Hash size={12} />
                      {domain}
                      <button
                        type="button"
                        onClick={() => removeDomain(domain)}
                        className="ml-1 hover:text-red-400"
                      >
                        <X size={12} />
                      </button>
                    </span>
                  ))}
                </div>
              </div>

              <div>
                <label className="block text-xs text-white/50 uppercase tracking-wider mb-2">
                  Tags
                </label>
                <div className="flex gap-2 mb-2">
                  <input
                    type="text"
                    value={tagInput}
                    onChange={(e) => setTagInput(e.target.value)}
                    onKeyPress={(e) => e.key === 'Enter' && (e.preventDefault(), addTag())}
                    placeholder="e.g., diet, budget, health"
                    className="flex-1 bg-white/5 border border-white/10 rounded-lg px-3 py-2 text-sm placeholder:text-white/30 focus:outline-none focus:border-phoenix-500/50"
                  />
                  <button
                    type="button"
                    onClick={addTag}
                    className="px-3 py-2 bg-white/10 hover:bg-white/20 rounded-lg transition-colors"
                  >
                    <Plus size={16} />
                  </button>
                </div>
                <div className="flex flex-wrap gap-2">
                  {formData.tags.map(tag => (
                    <span
                      key={tag}
                      className="flex items-center gap-1 px-2 py-1 bg-purple-500/20 text-purple-400 rounded-lg text-xs"
                    >
                      <Tag size={12} />
                      {tag}
                      <button
                        type="button"
                        onClick={() => removeTag(tag)}
                        className="ml-1 hover:text-red-400"
                      >
                        <X size={12} />
                      </button>
                    </span>
                  ))}
                </div>
              </div>

              <div className="flex justify-end gap-2">
                <button
                  type="button"
                  onClick={() => {
                    setShowForm(false);
                    resetForm();
                  }}
                  className="px-4 py-2 bg-white/10 hover:bg-white/20 rounded-lg transition-colors"
                >
                  Cancel
                </button>
                <motion.button
                  type="submit"
                  whileHover={{ scale: 1.05 }}
                  whileTap={{ scale: 0.95 }}
                  disabled={loading || !formData.text.trim()}
                  className="flex items-center gap-2 px-4 py-2 bg-phoenix-500 hover:bg-phoenix-600 rounded-lg font-medium disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
                >
                  <Save size={18} />
                  Create Card
                </motion.button>
              </div>
            </form>
          </motion.div>
        )}
      </AnimatePresence>

      {/* Cards List */}
      <div className="space-y-3 max-h-96 overflow-auto">
        {loading && cards.length === 0 ? (
          <div className="text-center text-white/30 py-8">Loading...</div>
        ) : cards.length === 0 ? (
          <div className="text-center text-white/30 py-8">
            No memory cards yet. Create one to get started!
          </div>
        ) : (
          cards.map(card => (
            <motion.div
              key={card.id}
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              className="p-4 bg-white/5 rounded-xl border border-white/10 hover:bg-white/10 transition-colors"
            >
              <div className="flex justify-between items-start mb-2">
                <div className="flex items-center gap-2">
                  <span className={`px-2 py-1 rounded-lg text-xs font-medium border ${getTypeColor(card.type)}`}>
                    {card.type}
                  </span>
                  {getPriorityBadge(card.priority)}
                </div>
                <button
                  onClick={() => handleDelete(card.id)}
                  className="p-1.5 hover:bg-red-500/20 rounded-lg transition-colors text-red-400"
                  title="Delete card"
                >
                  <Trash2 size={16} />
                </button>
              </div>
              <p className="text-white/90 mb-3">{card.text}</p>
              <div className="flex flex-wrap gap-2">
                {card.domain.map(domain => (
                  <span
                    key={domain}
                    className="flex items-center gap-1 px-2 py-0.5 bg-phoenix-500/20 text-phoenix-400 rounded text-xs"
                  >
                    <Hash size={10} />
                    {domain}
                  </span>
                ))}
                {card.tags.map(tag => (
                  <span
                    key={tag}
                    className="flex items-center gap-1 px-2 py-0.5 bg-purple-500/20 text-purple-400 rounded text-xs"
                  >
                    <Tag size={10} />
                    {tag}
                  </span>
                ))}
              </div>
              <div className="mt-2 text-xs text-white/40">
                Created: {new Date(card.created_at).toLocaleString()}
              </div>
            </motion.div>
          ))
        )}
      </div>
    </motion.div>
  );
};

export default MemoryCardManager;

