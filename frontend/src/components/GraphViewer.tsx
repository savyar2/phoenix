import React, { useRef, useState, useCallback, useEffect } from 'react';
import ForceGraph2D from 'react-force-graph-2d';
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
  User: '#f97316', Person: '#f97316', Preference: '#22c55e', Constraint: '#ef4444',
  Goal: '#3b82f6', Restaurant: '#a855f7', Diet: '#f59e0b', Budget: '#06b6d4',
  Action: '#8b5cf6', Entity: '#6b7280', preference: '#22c55e', constraint: '#ef4444',
  goal: '#3b82f6', capability: '#a855f7',
};

const GraphViewer: React.FC<GraphViewerProps> = ({ nodes, edges, highlightedNode, onNodeClick, onCardCreated }) => {
  const graphRef = useRef<any>();
  const [hoveredNode, setHoveredNode] = useState<GraphNode | null>(null);
  const [showCardForm, setShowCardForm] = useState(false);
  const [memoryCards, setMemoryCards] = useState<MemoryCard[]>([]);
  const [selectedPersona, setSelectedPersona] = useState('Personal');
  const [formData, setFormData] = useState<CreateMemoryCardRequest>({ type: 'preference', text: '', domain: [], priority: 'soft', tags: [], persona: 'Personal' });
  const [domainInput, setDomainInput] = useState('');
  const [tagInput, setTagInput] = useState('');
  const [loading, setLoading] = useState(false);

  const fetchMemoryCards = useCallback(async () => {
    try {
      const response = await memoryCardsApi.list(selectedPersona);
      setMemoryCards(response.data.cards || []);
    } catch (error) {
      console.error('Failed to fetch memory cards:', error);
    }
  }, [selectedPersona]);

  useEffect(() => { fetchMemoryCards(); }, [fetchMemoryCards]);

  const allNodes = React.useMemo(() => {
    const cardNodes: GraphNode[] = memoryCards.map(card => ({
      id: `card_${card.id}`,
      label: card.text.length > 20 ? card.text.substring(0, 20) + '...' : card.text,
      type: card.type,
      properties: { fullText: card.text, priority: card.priority, domains: card.domain, tags: card.tags },
      isMemoryCard: true,
    }));
    const cardEdges: GraphEdge[] = memoryCards.filter(card => card.domain.length > 0).map(card => ({
      source: 'demo_user', target: `card_${card.id}`, type: 'HAS_MEMORY_CARD',
    }));
    return { nodes: [...nodes, ...cardNodes], edges: [...edges, ...cardEdges] };
  }, [nodes, edges, memoryCards]);

  const handleZoomIn = () => graphRef.current?.zoom(1.5, 200);
  const handleZoomOut = () => graphRef.current?.zoom(0.67, 200);
  const handleReset = () => graphRef.current?.zoomToFit(200);

  const handleCreateCard = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      setLoading(true);
      await memoryCardsApi.create(formData);
      setShowCardForm(false);
      setFormData({ type: 'preference', text: '', domain: [], priority: 'soft', tags: [], persona: selectedPersona });
      setDomainInput(''); setTagInput('');
      await fetchMemoryCards();
      onCardCreated?.();
    } catch (error) {
      console.error('Failed to create memory card:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleDeleteCard = async (cardId: string) => {
    if (!confirm('Delete this card?')) return;
    try {
      await memoryCardsApi.delete(cardId);
      await fetchMemoryCards();
      onCardCreated?.();
    } catch (error) {
      console.error('Failed to delete:', error);
    }
  };

  const addDomain = () => {
    if (domainInput.trim() && !formData.domain.includes(domainInput.trim())) {
      setFormData({ ...formData, domain: [...formData.domain, domainInput.trim()] });
      setDomainInput('');
    }
  };

  const addTag = () => {
    if (tagInput.trim() && !formData.tags.includes(tagInput.trim())) {
      setFormData({ ...formData, tags: [...formData.tags, tagInput.trim()] });
      setTagInput('');
    }
  };

  const nodeColor = useCallback((node: GraphNode) => highlightedNode === node.id ? '#fff' : NODE_COLORS[node.type] || NODE_COLORS.Entity, [highlightedNode]);

  const nodeCanvasObject = useCallback((node: GraphNode, ctx: CanvasRenderingContext2D, globalScale: number) => {
    const label = node.label || node.id;
    const fontSize = Math.max(11 / globalScale, 3);
    const nodeSize = node.isMemoryCard ? 7 : 5;
    ctx.beginPath();
    ctx.arc(node.x!, node.y!, nodeSize, 0, 2 * Math.PI);
    ctx.fillStyle = nodeColor(node);
    ctx.fill();
    ctx.font = `${fontSize}px sans-serif`;
    ctx.textAlign = 'center';
    ctx.fillStyle = 'rgba(255,255,255,0.8)';
    ctx.fillText(label, node.x!, node.y! + nodeSize + fontSize);
  }, [nodeColor]);

  const linkColor = useCallback((link: GraphEdge) => {
    if (link.type === 'CONFLICTS_WITH') return '#ef4444';
    if (link.type === 'HAS_CONSTRAINT' || link.type === 'HAS_GOAL' || link.type === 'HAS_MEMORY_CARD') return '#f59e0b';
    return 'rgba(255,255,255,0.15)';
  }, []);

  const cardTypes = ['constraint', 'preference', 'goal', 'capability'] as const;

  return (
    <div className="glass-panel p-3 h-full w-full flex flex-col relative overflow-hidden">
      <div className="flex justify-between items-center mb-2 flex-shrink-0">
        <h2 className="text-sm font-semibold flex items-center gap-2">
          <span className="text-lg">💎</span> Memory Graph
        </h2>
        <div className="flex items-center gap-2">
          <select value={selectedPersona} onChange={(e) => setSelectedPersona(e.target.value)} className="bg-white/5 border border-white/10 rounded px-2 py-1 text-xs">
            <option value="Personal">Personal</option>
            <option value="Work">Work</option>
            <option value="Travel">Travel</option>
          </select>
          <button onClick={handleZoomIn} className="p-1.5 rounded bg-white/10 hover:bg-white/20"><ZoomIn size={14} /></button>
          <button onClick={handleZoomOut} className="p-1.5 rounded bg-white/10 hover:bg-white/20"><ZoomOut size={14} /></button>
          <button onClick={handleReset} className="p-1.5 rounded bg-white/10 hover:bg-white/20"><Maximize2 size={14} /></button>
        </div>
      </div>
      
      <div className="flex-1 rounded overflow-hidden bg-black/30 relative min-h-0">
        <ForceGraph2D
          ref={graphRef}
          graphData={{ nodes: allNodes.nodes, links: allNodes.edges }}
          nodeLabel="label"
          nodeColor={nodeColor}
          nodeCanvasObject={nodeCanvasObject}
          linkColor={linkColor}
          linkDirectionalArrowLength={3}
          linkDirectionalArrowRelPos={1}
          linkCurvature={0.1}
          onNodeClick={(node) => onNodeClick?.(node as GraphNode)}
          onNodeHover={(node) => setHoveredNode(node as GraphNode)}
          backgroundColor="transparent"
          cooldownTicks={30}
          warmupTicks={10}
        />
        <button onClick={() => setShowCardForm(true)} className="absolute bottom-3 right-3 w-10 h-10 bg-phoenix-500 hover:bg-phoenix-600 rounded-full shadow-lg flex items-center justify-center z-10">
          <Plus size={20} />
        </button>
      </div>
      
      {/* Legend */}
      <div className="absolute bottom-4 left-4 flex gap-2 text-xs z-10">
        {['Preference', 'Constraint', 'Goal'].map(type => (
          <div key={type} className="flex items-center gap-1">
            <div className="w-2 h-2 rounded-full" style={{ backgroundColor: NODE_COLORS[type] }} />
            <span className="text-white/50">{type}</span>
          </div>
        ))}
      </div>
      
      {/* Hover info */}
      {hoveredNode && (
        <div className="absolute top-12 right-3 bg-black/90 p-2 rounded text-xs max-w-[180px] z-10 border border-white/10">
          <div className="font-medium truncate">{hoveredNode.label}</div>
          <div className="text-white/50">{hoveredNode.type}</div>
          {hoveredNode.isMemoryCard && hoveredNode.properties?.fullText && (
            <div className="text-white/70 mt-1 line-clamp-2">{hoveredNode.properties.fullText as string}</div>
          )}
          {hoveredNode.id.startsWith('card_') && (
            <button onClick={() => handleDeleteCard(hoveredNode.id.replace('card_', ''))} className="mt-1.5 px-1.5 py-0.5 text-xs bg-red-500/20 text-red-400 rounded flex items-center gap-1">
              <Trash2 size={10} /> Delete
            </button>
          )}
        </div>
      )}

      {/* Card Form Modal */}
      {showCardForm && (
        <div className="absolute inset-0 bg-black/80 z-20 flex items-center justify-center p-3" onClick={(e) => e.target === e.currentTarget && setShowCardForm(false)}>
          <div className="bg-cyber-darker border border-white/20 rounded-lg p-4 w-full max-w-sm" onClick={(e) => e.stopPropagation()}>
            <div className="flex justify-between items-center mb-3">
              <h3 className="text-base font-semibold">Add Memory Card</h3>
              <button onClick={() => setShowCardForm(false)} className="p-1 hover:bg-white/10 rounded"><X size={16} /></button>
            </div>
            <form onSubmit={handleCreateCard} className="space-y-3">
              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-xs text-white/50 uppercase mb-1">Type</label>
                  <select value={formData.type} onChange={(e) => setFormData({ ...formData, type: e.target.value as any })} className="w-full bg-white/5 border border-white/10 rounded px-2 py-1.5 text-xs">
                    {cardTypes.map(type => <option key={type} value={type}>{type}</option>)}
                  </select>
                </div>
                <div>
                  <label className="block text-xs text-white/50 uppercase mb-1">Priority</label>
                  <select value={formData.priority} onChange={(e) => setFormData({ ...formData, priority: e.target.value as 'hard' | 'soft' })} className="w-full bg-white/5 border border-white/10 rounded px-2 py-1.5 text-xs">
                    <option value="soft">Soft</option>
                    <option value="hard">Hard</option>
                  </select>
                </div>
              </div>
              <div>
                <label className="block text-xs text-white/50 uppercase mb-1">Text</label>
                <textarea value={formData.text} onChange={(e) => setFormData({ ...formData, text: e.target.value })} placeholder="Enter constraint, preference..." required rows={2} className="w-full bg-white/5 border border-white/10 rounded px-2 py-1.5 text-xs placeholder:text-white/30" />
              </div>
              <div>
                <label className="block text-xs text-white/50 uppercase mb-1">Domains</label>
                <div className="flex gap-1 mb-1">
                  <input type="text" value={domainInput} onChange={(e) => setDomainInput(e.target.value)} onKeyPress={(e) => e.key === 'Enter' && (e.preventDefault(), addDomain())} placeholder="food, shopping..." className="flex-1 bg-white/5 border border-white/10 rounded px-2 py-1 text-xs" />
                  <button type="button" onClick={addDomain} className="px-2 bg-white/10 rounded"><Plus size={12} /></button>
                </div>
                <div className="flex flex-wrap gap-1">
                  {formData.domain.map(d => (
                    <span key={d} className="flex items-center gap-1 px-1.5 py-0.5 bg-phoenix-500/20 text-phoenix-400 rounded text-xs">
                      <Hash size={10} />{d}
                      <button type="button" onClick={() => setFormData({ ...formData, domain: formData.domain.filter(x => x !== d) })}><X size={10} /></button>
                    </span>
                  ))}
                </div>
              </div>
              <div>
                <label className="block text-xs text-white/50 uppercase mb-1">Tags</label>
                <div className="flex gap-1 mb-1">
                  <input type="text" value={tagInput} onChange={(e) => setTagInput(e.target.value)} onKeyPress={(e) => e.key === 'Enter' && (e.preventDefault(), addTag())} placeholder="diet, budget..." className="flex-1 bg-white/5 border border-white/10 rounded px-2 py-1 text-xs" />
                  <button type="button" onClick={addTag} className="px-2 bg-white/10 rounded"><Plus size={12} /></button>
                </div>
                <div className="flex flex-wrap gap-1">
                  {formData.tags.map(t => (
                    <span key={t} className="flex items-center gap-1 px-1.5 py-0.5 bg-purple-500/20 text-purple-400 rounded text-xs">
                      <Tag size={10} />{t}
                      <button type="button" onClick={() => setFormData({ ...formData, tags: formData.tags.filter(x => x !== t) })}><X size={10} /></button>
                    </span>
                  ))}
                </div>
              </div>
              <div className="flex justify-end gap-2 pt-1">
                <button type="button" onClick={() => setShowCardForm(false)} className="px-3 py-1.5 bg-white/10 rounded text-xs">Cancel</button>
                <button type="submit" disabled={loading || !formData.text.trim()} className="px-3 py-1.5 bg-phoenix-500 rounded text-xs font-medium disabled:opacity-50">Create</button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};

export default GraphViewer;
