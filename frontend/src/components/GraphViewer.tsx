import React, { useRef, useEffect, useState, useCallback } from 'react';
import ForceGraph2D from 'react-force-graph-2d';
import { motion, AnimatePresence } from 'framer-motion';
import { ZoomIn, ZoomOut, Maximize2, Plus, X, Tag, Hash, Trash2 } from 'lucide-react';
import { memoryCardsApi, MemoryCard, CreateMemoryCardRequest } from '../services/api';

interface GraphNode {
  id: string;
  label: string;
  type: string;
  properties?: Record<string, unknown>;
  x?: number;
  y?: number;
  isMemoryCard?: boolean;
}

interface GraphEdge {
  source: string | GraphNode;
  target: string | GraphNode;
  type: string;
}

interface GraphViewerProps {
  nodes: GraphNode[];
  edges: GraphEdge[];
  highlightedNode?: string;
  onNodeClick?: (node: GraphNode) => void;
  onCardCreated?: () => void;
}

const NODE_COLORS: Record<string, string> = {
  User: '#f97316',
  Person: '#f97316',
  Preference: '#22c55e',
  Constraint: '#ef4444',
  Goal: '#3b82f6',
  Restaurant: '#a855f7',
  Diet: '#f59e0b',
  Budget: '#06b6d4',
  Action: '#8b5cf6',
  Entity: '#6b7280',
  // Memory card types
  preference: '#22c55e',
  constraint: '#ef4444',
  goal: '#3b82f6',
  capability: '#a855f7',
};

const GraphViewer: React.FC<GraphViewerProps> = ({
  nodes,
  edges,
  highlightedNode,
  onNodeClick,
  onCardCreated,
}) => {
  const graphRef = useRef<any>();
  const [hoveredNode, setHoveredNode] = useState<GraphNode | null>(null);
  const [showCardForm, setShowCardForm] = useState(false);
  const [memoryCards, setMemoryCards] = useState<MemoryCard[]>([]);
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
  const [loading, setLoading] = useState(false);

  // Fetch memory cards
  const fetchMemoryCards = useCallback(async () => {
    try {
      const response = await memoryCardsApi.list(selectedPersona);
      setMemoryCards(response.data.cards || []);
    } catch (error) {
      console.error('Failed to fetch memory cards:', error);
    }
  }, [selectedPersona]);

  useEffect(() => {
    fetchMemoryCards();
  }, [fetchMemoryCards]);

  // Merge memory cards with graph nodes
  const allNodes = React.useMemo(() => {
    const cardNodes: GraphNode[] = memoryCards.map(card => ({
      id: `card_${card.id}`,
      label: card.text.length > 30 ? card.text.substring(0, 30) + '...' : card.text,
      type: card.type,
      properties: {
        fullText: card.text,
        priority: card.priority,
        domains: card.domain,
        tags: card.tags,
        persona: card.persona,
      },
      isMemoryCard: true,
    }));

    // Create edges from memory cards to user if they have domains
    const cardEdges: GraphEdge[] = memoryCards
      .filter(card => card.domain.length > 0)
      .map(card => ({
        source: 'demo_user',
        target: `card_${card.id}`,
        type: 'HAS_MEMORY_CARD',
      }));

    return {
      nodes: [...nodes, ...cardNodes],
      edges: [...edges, ...cardEdges],
    };
  }, [nodes, edges, memoryCards]);

  const handleZoomIn = () => {
    graphRef.current?.zoom(1.5, 400);
  };

  const handleZoomOut = () => {
    graphRef.current?.zoom(0.67, 400);
  };

  const handleReset = () => {
    graphRef.current?.zoomToFit(400);
  };

  const handleCreateCard = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      setLoading(true);
      await memoryCardsApi.create(formData);
      setShowCardForm(false);
      resetForm();
      await fetchMemoryCards();
      onCardCreated?.();
    } catch (error) {
      console.error('Failed to create memory card:', error);
      alert('Failed to create memory card. Check console for details.');
    } finally {
      setLoading(false);
    }
  };

  const handleDeleteCard = async (cardId: string) => {
    if (!confirm('Are you sure you want to delete this memory card?')) return;
    try {
      await memoryCardsApi.delete(cardId);
      await fetchMemoryCards();
      onCardCreated?.();
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
      persona: selectedPersona,
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

  const nodeColor = useCallback((node: GraphNode) => {
    if (highlightedNode === node.id) {
      return '#fff';
    }
    if (node.isMemoryCard) {
      return NODE_COLORS[node.type] || NODE_COLORS.Entity;
    }
    return NODE_COLORS[node.type] || NODE_COLORS.Entity;
  }, [highlightedNode]);

  const nodeCanvasObject = useCallback((node: GraphNode, ctx: CanvasRenderingContext2D, globalScale: number) => {
    const label = node.label || node.id;
    const fontSize = 12 / globalScale;
    const nodeSize = highlightedNode === node.id ? 10 : node.isMemoryCard ? 8 : 6;
    
    // Node circle
    ctx.beginPath();
    ctx.arc(node.x!, node.y!, nodeSize, 0, 2 * Math.PI);
    ctx.fillStyle = nodeColor(node);
    ctx.fill();
    
    // Glow effect for highlighted node or memory cards
    if (highlightedNode === node.id || node.isMemoryCard) {
      ctx.shadowColor = node.isMemoryCard ? NODE_COLORS[node.type] || '#f97316' : '#f97316';
      ctx.shadowBlur = 15;
      ctx.fill();
      ctx.shadowBlur = 0;
    }
    
    // Label
    ctx.font = `${fontSize}px 'Space Grotesk', sans-serif`;
    ctx.textAlign = 'center';
    ctx.textBaseline = 'middle';
    ctx.fillStyle = 'rgba(255, 255, 255, 0.9)';
    ctx.fillText(label, node.x!, node.y! + nodeSize + fontSize);
  }, [highlightedNode, nodeColor]);

  const linkColor = useCallback((link: GraphEdge) => {
    if (link.type === 'CONFLICTS_WITH') {
      return '#ef4444';
    }
    if (link.type === 'HAS_CONSTRAINT' || link.type === 'HAS_GOAL' || link.type === 'HAS_MEMORY_CARD') {
      return '#f59e0b';
    }
    return 'rgba(255, 255, 255, 0.3)';
  }, []);

  const cardTypes = ['constraint', 'preference', 'goal', 'capability'] as const;

  return (
    <motion.div
      className="glass-panel p-4 h-full flex flex-col relative"
      initial={{ opacity: 0, scale: 0.95 }}
      animate={{ opacity: 1, scale: 1 }}
      transition={{ duration: 0.5 }}
    >
      <div className="flex justify-between items-center mb-4">
        <h2 className="text-lg font-semibold flex items-center gap-2">
          <span className="text-2xl">💎</span>
          Memory Graph
        </h2>
        <div className="flex items-center gap-2">
          <select
            value={selectedPersona}
            onChange={(e) => setSelectedPersona(e.target.value)}
            className="bg-white/5 border border-white/10 rounded-lg px-2 py-1 text-xs focus:outline-none focus:border-phoenix-500/50"
          >
            <option value="Personal">Personal</option>
            <option value="Work">Work</option>
            <option value="Travel">Travel</option>
          </select>
          <div className="flex gap-2">
            <button
              onClick={handleZoomIn}
              className="p-2 rounded-lg bg-white/10 hover:bg-white/20 transition-colors"
              aria-label="Zoom in"
            >
              <ZoomIn size={16} />
            </button>
            <button
              onClick={handleZoomOut}
              className="p-2 rounded-lg bg-white/10 hover:bg-white/20 transition-colors"
              aria-label="Zoom out"
            >
              <ZoomOut size={16} />
            </button>
            <button
              onClick={handleReset}
              className="p-2 rounded-lg bg-white/10 hover:bg-white/20 transition-colors"
              aria-label="Reset view"
            >
              <Maximize2 size={16} />
            </button>
          </div>
        </div>
      </div>
      
      <div className="h-[calc(100%-60px)] rounded-xl overflow-hidden bg-black/30 relative">
        <ForceGraph2D
          ref={graphRef}
          graphData={{ nodes: allNodes.nodes, links: allNodes.edges }}
          nodeLabel="label"
          nodeColor={nodeColor}
          nodeCanvasObject={nodeCanvasObject}
          linkColor={linkColor}
          linkDirectionalArrowLength={4}
          linkDirectionalArrowRelPos={1}
          linkCurvature={0.2}
          onNodeClick={(node) => onNodeClick?.(node as GraphNode)}
          onNodeHover={(node) => setHoveredNode(node as GraphNode)}
          backgroundColor="transparent"
          cooldownTicks={100}
        />

        {/* Floating Add Card Button */}
        <motion.button
          whileHover={{ scale: 1.1 }}
          whileTap={{ scale: 0.9 }}
          onClick={() => setShowCardForm(true)}
          className="absolute bottom-4 right-4 w-12 h-12 bg-phoenix-500 hover:bg-phoenix-600 rounded-full shadow-lg shadow-phoenix-500/50 flex items-center justify-center transition-colors z-10"
          title="Add Memory Card"
        >
          <Plus size={24} />
        </motion.button>
      </div>
      
      {/* Legend */}
      <div className="absolute bottom-6 left-6 flex flex-wrap gap-3 text-xs z-10">
        {Object.entries(NODE_COLORS).slice(0, 5).map(([type, color]) => (
          <div key={type} className="flex items-center gap-1">
            <div
              className="w-3 h-3 rounded-full"
              style={{ backgroundColor: color }}
            />
            <span className="text-white/60">{type}</span>
          </div>
        ))}
      </div>
      
      {/* Hovered node info */}
      {hoveredNode && (
        <motion.div
          initial={{ opacity: 0, y: 10 }}
          animate={{ opacity: 1, y: 0 }}
          className="absolute top-20 right-6 bg-black/90 backdrop-blur-sm p-3 rounded-lg text-sm max-w-[250px] z-10 border border-white/10"
        >
          <div className="font-semibold">{hoveredNode.label}</div>
          <div className="text-white/60 text-xs mt-1">Type: {hoveredNode.type}</div>
          {hoveredNode.isMemoryCard && hoveredNode.properties && (
            <div className="mt-2 pt-2 border-t border-white/10">
              {hoveredNode.properties.fullText && (
                <div className="text-xs text-white/80 mb-1">{hoveredNode.properties.fullText as string}</div>
              )}
              {hoveredNode.properties.domains && (hoveredNode.properties.domains as string[]).length > 0 && (
                <div className="flex flex-wrap gap-1 mt-1">
                  {(hoveredNode.properties.domains as string[]).map((domain: string) => (
                    <span key={domain} className="text-xs px-1.5 py-0.5 bg-phoenix-500/20 text-phoenix-400 rounded">
                      {domain}
                    </span>
                  ))}
                </div>
              )}
              {hoveredNode.properties.priority && (
                <div className="text-xs mt-1">
                  Priority: <span className="text-phoenix-400">{hoveredNode.properties.priority as string}</span>
                </div>
              )}
              {hoveredNode.id.startsWith('card_') && (
                <button
                  onClick={() => handleDeleteCard(hoveredNode.id.replace('card_', ''))}
                  className="mt-2 px-2 py-1 text-xs bg-red-500/20 hover:bg-red-500/30 text-red-400 rounded transition-colors"
                >
                  <Trash2 size={12} className="inline mr-1" />
                  Delete
                </button>
              )}
            </div>
          )}
        </motion.div>
      )}

      {/* Memory Card Creation Form Modal */}
      <AnimatePresence>
        {showCardForm && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="absolute inset-0 bg-black/80 backdrop-blur-sm z-20 flex items-center justify-center p-4"
            onClick={(e) => e.target === e.currentTarget && setShowCardForm(false)}
          >
            <motion.div
              initial={{ scale: 0.9, opacity: 0 }}
              animate={{ scale: 1, opacity: 1 }}
              exit={{ scale: 0.9, opacity: 0 }}
              className="bg-cyber-darker border border-white/20 rounded-2xl p-6 max-w-lg w-full max-h-[90vh] overflow-y-auto"
              onClick={(e) => e.stopPropagation()}
            >
              <div className="flex justify-between items-center mb-4">
                <h3 className="text-xl font-semibold">Create Memory Card</h3>
                <button
                  onClick={() => {
                    setShowCardForm(false);
                    resetForm();
                  }}
                  className="p-1 hover:bg-white/10 rounded-lg transition-colors"
                >
                  <X size={20} />
                </button>
              </div>

              <form onSubmit={handleCreateCard} className="space-y-4">
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

                <div className="flex justify-end gap-2 pt-4">
                  <button
                    type="button"
                    onClick={() => {
                      setShowCardForm(false);
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
                    <Plus size={18} />
                    Create Card
                  </motion.button>
                </div>
              </form>
            </motion.div>
          </motion.div>
        )}
      </AnimatePresence>
    </motion.div>
  );
};

export default GraphViewer;
