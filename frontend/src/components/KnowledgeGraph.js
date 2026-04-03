'use client';

import { useEffect, useRef, useState } from 'react';
import * as d3 from 'd3';

export default function KnowledgeGraph({ data, width = 900, height = 600 }) {
  const svgRef = useRef(null);
  const [tooltip, setTooltip] = useState(null);

  /* D3.js color mapping for priority groups */
  const groupColors = {
    1: '#ef4444', // HIGH PRIORITY - red
    2: '#f59e0b', // MEDIUM PRIORITY - amber
    3: '#10b981', // LOW PRIORITY - green
  };

  useEffect(() => {
    if (!data || !data.nodes || !data.links) return;

    const svg = d3.select(svgRef.current);
    svg.selectAll('*').remove();

    const g = svg.append('g');

    // ── Zoom Behavior ─────────────────────────────
    const zoom = d3.zoom()
      .scaleExtent([0.3, 4])
      .on('zoom', (event) => g.attr('transform', event.transform));
    svg.call(zoom);

    // ── Arrow Markers ─────────────────────────────
    svg.append('defs').selectAll('marker')
      .data(['prerequisite', 'dependency', 'correlation'])
      .join('marker')
      .attr('id', d => `arrow-${d}`)
      .attr('viewBox', '0 -5 10 10')
      .attr('refX', 25)
      .attr('refY', 0)
      .attr('markerWidth', 8)
      .attr('markerHeight', 8)
      .attr('orient', 'auto')
      .append('path')
      .attr('d', 'M0,-5L10,0L0,5')
      .attr('fill', d => d === 'prerequisite' ? '#8b5cf6' : d === 'dependency' ? '#3b82f6' : '#6b7280');

    // ── Force Simulation ──────────────────────────
    const simulation = d3.forceSimulation(data.nodes)
      .force('link', d3.forceLink(data.links)
        .id(d => d.id)
        .distance(d => 100 + (1 - d.weight) * 100)
        .strength(d => d.weight * 0.5)
      )
      .force('charge', d3.forceManyBody().strength(-300))
      .force('center', d3.forceCenter(width / 2, height / 2))
      .force('collision', d3.forceCollide().radius(d => getNodeRadius(d) + 5));

    // ── Links ─────────────────────────────────────
    const link = g.append('g')
      .selectAll('line')
      .data(data.links)
      .join('line')
      .attr('stroke', d => {
        if (d.type === 'prerequisite') return '#8b5cf680';
        if (d.type === 'dependency') return '#3b82f680';
        return '#6b728060';
      })
      .attr('stroke-width', d => Math.max(1, d.weight * 3))
      .attr('stroke-dasharray', d => d.type === 'correlation' ? '5,5' : 'none')
      .attr('marker-end', d => `url(#arrow-${d.type})`);

    // ── Nodes ─────────────────────────────────────
    const node = g.append('g')
      .selectAll('g')
      .data(data.nodes)
      .join('g')
      .call(d3.drag()
        .on('start', (event, d) => {
          if (!event.active) simulation.alphaTarget(0.3).restart();
          d.fx = d.x;
          d.fy = d.y;
        })
        .on('drag', (event, d) => {
          d.fx = event.x;
          d.fy = event.y;
        })
        .on('end', (event, d) => {
          if (!event.active) simulation.alphaTarget(0);
          d.fx = null;
          d.fy = null;
        })
      );

    // Node circles with glow
    node.append('circle')
      .attr('r', d => getNodeRadius(d))
      .attr('fill', d => groupColors[d.group] || '#6b7280')
      .attr('fill-opacity', 0.8)
      .attr('stroke', d => groupColors[d.group] || '#6b7280')
      .attr('stroke-width', 2)
      .attr('stroke-opacity', 0.4)
      .style('filter', 'drop-shadow(0 0 6px rgba(99,102,241,0.3))')
      .style('cursor', 'pointer')
      .on('mouseover', (event, d) => {
        d3.select(event.target)
          .transition().duration(200)
          .attr('r', getNodeRadius(d) * 1.3)
          .attr('fill-opacity', 1);

        setTooltip({
          x: event.pageX + 15,
          y: event.pageY - 10,
          name: d.name,
          score: d.probability_score,
          priority: d.priority,
          difficulty: d.difficulty,
          mastery: d.mastery_score,
        });
      })
      .on('mouseout', (event, d) => {
        d3.select(event.target)
          .transition().duration(200)
          .attr('r', getNodeRadius(d))
          .attr('fill-opacity', 0.8);
        setTooltip(null);
      });

    // Node labels
    node.append('text')
      .text(d => d.name.length > 18 ? d.name.substring(0, 18) + '...' : d.name)
      .attr('text-anchor', 'middle')
      .attr('dy', d => getNodeRadius(d) + 14)
      .attr('fill', '#a0a0cc')
      .attr('font-size', '11px')
      .attr('font-family', 'Inter, sans-serif')
      .attr('font-weight', 500)
      .style('pointer-events', 'none');

    // Score labels on nodes
    node.append('text')
      .text(d => d.probability_score > 0 ? `${Math.round(d.probability_score)}` : '')
      .attr('text-anchor', 'middle')
      .attr('dy', '4px')
      .attr('fill', '#fff')
      .attr('font-size', d => getNodeRadius(d) > 15 ? '11px' : '9px')
      .attr('font-family', 'Inter, sans-serif')
      .attr('font-weight', 800)
      .style('pointer-events', 'none');

    // ── Tick ──────────────────────────────────────
    simulation.on('tick', () => {
      link
        .attr('x1', d => d.source.x)
        .attr('y1', d => d.source.y)
        .attr('x2', d => d.target.x)
        .attr('y2', d => d.target.y);

      node.attr('transform', d => `translate(${d.x},${d.y})`);
    });

    return () => simulation.stop();
  }, [data, width, height]);

  function getNodeRadius(d) {
    const base = 12;
    const scoreBonus = (d.probability_score || 0) / 100 * 16;
    return base + scoreBonus;
  }

  return (
    <div className="graph-container" style={{ position: 'relative' }}>
      <svg
        ref={svgRef}
        width={width}
        height={height}
        style={{ background: 'var(--bg-secondary)' }}
      />

      {/* Legend */}
      <div style={{
        position: 'absolute',
        top: '12px',
        left: '12px',
        background: 'var(--bg-glass)',
        backdropFilter: 'blur(12px)',
        border: '1px solid var(--border-color)',
        borderRadius: 'var(--radius-sm)',
        padding: '12px',
        fontSize: '11px',
      }}>
        <div style={{ fontWeight: 700, marginBottom: '8px', color: 'var(--text-primary)' }}>Legend</div>
        {[
          { color: '#ef4444', label: 'High Priority' },
          { color: '#f59e0b', label: 'Medium Priority' },
          { color: '#10b981', label: 'Low Priority' },
        ].map((item, i) => (
          <div key={i} style={{ display: 'flex', alignItems: 'center', gap: '6px', marginBottom: '4px' }}>
            <div style={{ width: '10px', height: '10px', borderRadius: '50%', background: item.color }} />
            <span style={{ color: 'var(--text-secondary)' }}>{item.label}</span>
          </div>
        ))}
        <div style={{ marginTop: '8px', borderTop: '1px solid var(--border-color)', paddingTop: '8px' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '6px', marginBottom: '4px' }}>
            <div style={{ width: '20px', height: '2px', background: '#8b5cf6' }} />
            <span style={{ color: 'var(--text-muted)' }}>Prerequisite</span>
          </div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '6px', marginBottom: '4px' }}>
            <div style={{ width: '20px', height: '2px', background: '#3b82f6' }} />
            <span style={{ color: 'var(--text-muted)' }}>Dependency</span>
          </div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
            <div style={{ width: '20px', height: '2px', background: '#6b7280', borderBottom: '2px dashed #6b7280' }} />
            <span style={{ color: 'var(--text-muted)' }}>Correlation</span>
          </div>
        </div>
      </div>

      {/* Tooltip */}
      {tooltip && (
        <div className="graph-tooltip" style={{ left: tooltip.x, top: tooltip.y }}>
          <div style={{ fontWeight: 700, fontSize: '14px', marginBottom: '6px', color: 'var(--text-primary)' }}>
            {tooltip.name}
          </div>
          <div style={{ color: 'var(--text-secondary)' }}>
            Score: <strong style={{ color: tooltip.score >= 70 ? '#ef4444' : tooltip.score >= 40 ? '#f59e0b' : '#10b981' }}>{tooltip.score}</strong>/100
          </div>
          <div style={{ color: 'var(--text-secondary)' }}>Priority: {tooltip.priority}</div>
          <div style={{ color: 'var(--text-secondary)' }}>Difficulty: {tooltip.difficulty}</div>
        </div>
      )}
    </div>
  );
}
