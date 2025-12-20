import React from 'react';
import { FaUser, FaSpinner } from 'react-icons/fa';
import { useAuth } from '../../context/AuthContext';
import './MessageDisplay.css';

// Simple Chart Component for Graph Mode
const SimpleChart = ({ data }) => {
    if (!data) {
        console.log('[SimpleChart] No data provided');
        return <div className="chart-error">No visualization data available</div>;
    }
    
    console.log('[SimpleChart] Rendering chart with data:', data);
    
    const { chart_type, labels, values, category_label, value_label, title, value } = data;
    
    // Single value display
    if (chart_type === 'single_value') {
        return (
            <div className="single-value-chart">
                <div className="chart-title">{title || value_label}</div>
                <div className="chart-value">{typeof value === 'number' ? value.toLocaleString('en-IN') : value}</div>
            </div>
        );
    }
    
    if (!labels || !values || labels.length === 0 || values.length === 0) {
        console.log('[SimpleChart] Missing labels or values:', { labels, values });
        return <div className="chart-error">No data available for visualization</div>;
    }
    
    // Ensure values are numbers
    const numericValues = values.map(val => {
        if (typeof val === 'number') return val;
        if (typeof val === 'string') {
            const cleaned = val.replace(/[₹$,\s]/g, '').trim();
            const parsed = parseFloat(cleaned);
            return isNaN(parsed) ? 0 : parsed;
        }
        return 0;
    });
    
    const maxValue = Math.max(...numericValues, 1); // Ensure at least 1 to avoid division by zero
    const chartHeight = 350;
    
    console.log('[SimpleChart] Chart data:', {
        chart_type,
        labels_count: labels.length,
        values_count: numericValues.length,
        maxValue,
        sample_values: numericValues.slice(0, 3)
    });
    
    // Bar Chart
    if (chart_type === 'bar_chart') {
        // Calculate dimensions
        const svgWidth = Math.max(600, labels.length * 80);
        const padding = { top: 40, right: 50, bottom: 80, left: 60 };
        const chartAreaWidth = svgWidth - padding.left - padding.right;
        const chartAreaHeight = chartHeight - padding.top - padding.bottom;
        
        // Calculate bar dimensions
        const barSpacing = 10;
        const availableWidth = chartAreaWidth - (barSpacing * (labels.length - 1));
        const barWidth = Math.max(30, Math.min(80, availableWidth / labels.length));
        
        // Ensure maxValue is not zero
        const safeMaxValue = maxValue > 0 ? maxValue : 1;
        
        return (
            <div className="bar-chart-container">
                {title && <div className="chart-title">{title}</div>}
                <div className="chart-labels">
                    <span className="category-label">{category_label}</span>
                    <span className="value-label">{value_label}</span>
                </div>
                <div style={{ overflowX: 'auto', width: '100%' }}>
                    <svg width={svgWidth} height={chartHeight} className="bar-chart-svg" viewBox={`0 0 ${svgWidth} ${chartHeight}`}>
                        {/* Y-axis line */}
                        <line
                            x1={padding.left}
                            y1={padding.top}
                            x2={padding.left}
                            y2={chartHeight - padding.bottom}
                            stroke="var(--icon-color)"
                            strokeWidth="2"
                        />
                        
                        {/* X-axis line */}
                        <line
                            x1={padding.left}
                            y1={chartHeight - padding.bottom}
                            x2={svgWidth - padding.right}
                            y2={chartHeight - padding.bottom}
                            stroke="var(--icon-color)"
                            strokeWidth="2"
                        />
                        
                        {/* Y-axis labels (max value) */}
                        <text
                            x={padding.left - 10}
                            y={padding.top + 5}
                            textAnchor="end"
                            fontSize="11"
                            fill="var(--icon-color)"
                        >
                            {safeMaxValue.toLocaleString('en-IN')}
                        </text>
                        
                        {/* Y-axis label (0) */}
                        <text
                            x={padding.left - 10}
                            y={chartHeight - padding.bottom + 5}
                            textAnchor="end"
                            fontSize="11"
                            fill="var(--icon-color)"
                        >
                            0
                        </text>
                        
                        {/* Bars */}
                        {numericValues.map((val, idx) => {
                            const barHeight = maxValue > 0 ? (val / safeMaxValue) * chartAreaHeight : 0;
                            const x = padding.left + (idx * (barWidth + barSpacing));
                            const y = padding.top + chartAreaHeight - barHeight;
                            
                            // Format value for display
                            const displayValue = typeof val === 'number' ? val.toLocaleString('en-IN') : String(val);
                            
                            return (
                                <g key={idx}>
                                    {/* Bar */}
                                    <rect
                                        x={x}
                                        y={y}
                                        width={barWidth}
                                        height={barHeight}
                                        fill="var(--brand-color)"
                                        rx="4"
                                        style={{ transition: 'all 0.3s ease' }}
                                    />
                                    
                                    {/* Value label on top of bar */}
                                    {barHeight > 20 && (
                                        <text
                                            x={x + barWidth / 2}
                                            y={y - 5}
                                            textAnchor="middle"
                                            fontSize="11"
                                            fill="var(--text-color)"
                                            fontWeight="600"
                                        >
                                            {displayValue}
                                        </text>
                                    )}
                                    
                                    {/* Category label below bar */}
                                    <text
                                        x={x + barWidth / 2}
                                        y={chartHeight - padding.bottom + 20}
                                        textAnchor="middle"
                                        fontSize="10"
                                        fill="var(--text-color)"
                                        transform={`rotate(-45 ${x + barWidth / 2} ${chartHeight - padding.bottom + 20})`}
                                    >
                                        {labels[idx] || `Item ${idx + 1}`}
                                    </text>
                                </g>
                            );
                        })}
                    </svg>
                </div>
            </div>
        );
    }
    
    // Pie Chart
    if (chart_type === 'pie_chart') {
        const total = numericValues.reduce((sum, val) => sum + val, 0);
        if (total === 0) {
            return <div className="chart-error">No data to display in pie chart</div>;
        }
        let currentAngle = -90; // Start from top
        
        return (
            <div className="pie-chart-container">
                {title && <div className="chart-title">{title}</div>}
                <svg width="300" height="300" className="pie-chart-svg">
                    <g transform="translate(150, 150)">
                        {numericValues.map((val, idx) => {
                            const percentage = (val / total) * 100;
                            const angle = (val / total) * 360;
                            const largeArc = angle > 180 ? 1 : 0;
                            
                            const x1 = Math.cos((currentAngle * Math.PI) / 180) * 100;
                            const y1 = Math.sin((currentAngle * Math.PI) / 180) * 100;
                            
                            currentAngle += angle;
                            
                            const x2 = Math.cos((currentAngle * Math.PI) / 180) * 100;
                            const y2 = Math.sin((currentAngle * Math.PI) / 180) * 100;
                            
                            const pathData = [
                                `M 0 0`,
                                `L ${x1} ${y1}`,
                                `A 100 100 0 ${largeArc} 1 ${x2} ${y2}`,
                                `Z`
                            ].join(' ');
                            
                            const labelX = Math.cos(((currentAngle - angle / 2) * Math.PI) / 180) * 120;
                            const labelY = Math.sin(((currentAngle - angle / 2) * Math.PI) / 180) * 120;
                            
                            return (
                                <g key={idx}>
                                    <path
                                        d={pathData}
                                        fill={`hsl(${(idx * 360) / values.length}, 70%, 50%)`}
                                        stroke="white"
                                        strokeWidth="2"
                                    />
                                    <text
                                        x={labelX}
                                        y={labelY}
                                        textAnchor="middle"
                                        fontSize="11"
                                        fill="var(--text-color)"
                                        fontWeight="bold"
                                    >
                                        {labels[idx]} ({percentage.toFixed(1)}%)
                                    </text>
                                </g>
                            );
                        })}
                    </g>
                </svg>
            </div>
        );
    }
    
    // Line Chart (simple implementation)
    if (chart_type === 'line_chart') {
        const svgWidth = Math.max(600, labels.length * 80);
        const padding = { top: 40, right: 50, bottom: 80, left: 60 };
        const chartAreaWidth = svgWidth - padding.left - padding.right;
        const chartAreaHeight = chartHeight - padding.top - padding.bottom;
        const safeMaxValue = maxValue > 0 ? maxValue : 1;
        
        const points = numericValues.map((val, idx) => {
            const x = padding.left + (idx / (numericValues.length - 1 || 1)) * chartAreaWidth;
            const y = padding.top + chartAreaHeight - ((val / safeMaxValue) * chartAreaHeight);
            return { x, y };
        });
        
        const pathData = points.map((point, idx) => 
            `${idx === 0 ? 'M' : 'L'} ${point.x} ${point.y}`
        ).join(' ');
        
        return (
            <div className="line-chart-container">
                {title && <div className="chart-title">{title}</div>}
                <div style={{ overflowX: 'auto', width: '100%' }}>
                    <svg width={svgWidth} height={chartHeight} className="line-chart-svg" viewBox={`0 0 ${svgWidth} ${chartHeight}`}>
                        {/* Y-axis line */}
                        <line
                            x1={padding.left}
                            y1={padding.top}
                            x2={padding.left}
                            y2={chartHeight - padding.bottom}
                            stroke="var(--icon-color)"
                            strokeWidth="2"
                        />
                        
                        {/* X-axis line */}
                        <line
                            x1={padding.left}
                            y1={chartHeight - padding.bottom}
                            x2={svgWidth - padding.right}
                            y2={chartHeight - padding.bottom}
                            stroke="var(--icon-color)"
                            strokeWidth="2"
                        />
                        
                        <path
                            d={pathData}
                            fill="none"
                            stroke="var(--brand-color)"
                            strokeWidth="3"
                        />
                        {points.map((point, idx) => (
                            <circle
                                key={idx}
                                cx={point.x}
                                cy={point.y}
                                r="5"
                                fill="var(--brand-color)"
                            />
                        ))}
                        {labels.map((label, idx) => {
                            const x = padding.left + (idx / (labels.length - 1 || 1)) * chartAreaWidth;
                            return (
                                <text
                                    key={idx}
                                    x={x}
                                    y={chartHeight - padding.bottom + 20}
                                    textAnchor="middle"
                                    fontSize="10"
                                    fill="var(--text-color)"
                                    transform={`rotate(-45 ${x} ${chartHeight - padding.bottom + 20})`}
                                >
                                    {label}
                                </text>
                            );
                        })}
                    </svg>
                </div>
            </div>
        );
    }
    
    return <div className="chart-error">Unsupported chart type: {chart_type}</div>;
};

const MessageDisplay = ({ messages, isLoading }) => {
    const { user } = useAuth();
    // Auto-scroll to bottom when new messages arrive
    const messagesEndRef = React.useRef(null);

    React.useEffect(() => {
        if (messagesEndRef.current) {
            messagesEndRef.current.scrollIntoView({ behavior: 'smooth' });
        }
    }, [messages, isLoading]);

    // Get user initial for avatar (same as ProfileSection)
    const userInitial = user?.name ? user.name.charAt(0).toUpperCase() : <FaUser />;

    // Only render container when there are messages or loading
    if ((!messages || messages.length === 0) && !isLoading) {
        return null;
    }

    return (
        <div className="messages-container">
            {messages && messages.length > 0 && messages.map((message, index) => (
                <div key={index} className={`message-wrapper ${message.type}`}>
                    <div className="message-avatar">
                        {message.type === 'user' ? (
                            <span className="avatar-initial">{userInitial}</span>
                        ) : (
                            <img src="/logo-dark.png" alt="Shreshthaa Logo" className="avatar-logo" />
                        )}
                    </div>
                    <div className="message-content">
                        {message.type === 'user' ? (
                            <div className="user-message">
                                {message.text}
                            </div>
                        ) : (
                            <div className="bot-message">
                                {/* Text Mode: Show answer as paragraph */}
                                {message.mode === 'text' && (
                                    <div className="bot-answer">{message.answer}</div>
                                )}
                                
                                {/* Graph Mode: Show visualization */}
                                {message.mode === 'graph' && message.visualization_data && (
                                    <div className="bot-visualization">
                                        <div className="bot-answer">{message.answer}</div>
                                        <div className="visualization-container">
                                            <SimpleChart data={message.visualization_data} />
                                        </div>
                                    </div>
                                )}
                                
                                {/* Table Mode: Show structured table */}
                                {message.mode === 'table' && message.table_data && (
                                    <div className="bot-table">
                                        {message.answer && (
                                            <div className="bot-answer table-mode-summary">{message.answer}</div>
                                        )}
                                        <div className="results-table table-mode-table">
                                            <table>
                                                <thead>
                                                    <tr>
                                                        {message.table_data.headers.map((header) => (
                                                            <th key={header}>{header}</th>
                                                        ))}
                                                    </tr>
                                                </thead>
                                                <tbody>
                                                    {message.table_data.rows.map((row, idx) => (
                                                        <tr key={idx}>
                                                            {row.map((cell, cellIdx) => (
                                                                <td key={cellIdx}>
                                                                    {cell !== null && cell !== undefined 
                                                                        ? String(cell) 
                                                                        : '-'}
                                                                </td>
                                                            ))}
                                                        </tr>
                                                    ))}
                                                </tbody>
                                            </table>
                                        </div>
                                    </div>
                                )}
                                
                                {/* Fallback: Show results table if mode is text and results exist */}
                                {message.mode === 'text' && message.results && message.results.length > 0 && (
                                    <div className="bot-results">
                                        <div className="results-header">Query Results:</div>
                                        <div className="results-table">
                                            <table>
                                                <thead>
                                                    <tr>
                                                        {Object.keys(message.results[0]).map((key) => (
                                                            <th key={key}>{key}</th>
                                                        ))}
                                                    </tr>
                                                </thead>
                                                <tbody>
                                                    {message.results.map((row, idx) => (
                                                        <tr key={idx}>
                                                            {Object.values(row).map((value, valIdx) => (
                                                                <td key={valIdx}>
                                                                    {value !== null && value !== undefined 
                                                                        ? String(value) 
                                                                        : '-'}
                                                                </td>
                                                            ))}
                                                        </tr>
                                                    ))}
                                                </tbody>
                                            </table>
                                        </div>
                                    </div>
                                )}
                            </div>
                        )}
                        <div className="message-time">
                            {new Date(message.timestamp).toLocaleTimeString([], { 
                                hour: '2-digit', 
                                minute: '2-digit' 
                            })}
                        </div>
                    </div>
                </div>
            ))}
            {isLoading && (
                <div className="message-wrapper bot">
                    <div className="message-avatar">
                        <img src="/logo-dark.png" alt="Shreshthaa Logo" className="avatar-logo" />
                    </div>
                    <div className="message-content">
                        <div className="bot-message">
                            <div className="loading-message">
                                <FaSpinner className="spinner-icon" />
                                Processing your query...
                            </div>
                        </div>
                    </div>
                </div>
            )}
            <div ref={messagesEndRef} />
        </div>
    );
};

export default MessageDisplay;

