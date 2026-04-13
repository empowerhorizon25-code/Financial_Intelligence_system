// AI Stock Signals - Revenue-Focused App js
// Tracks usage and enforces paywall

const DAILY_LIMIT = 3;
let currentAnalysis = null;
let backtestChart = null;

// ===== USAGE TRACKING =====
function getDailyUsage() {
    const today = new Date().toDateString();
    const stored = localStorage.getItem('ais-usage');
    
    if (!stored) {
        return { date: today, count: 0 };
    }
    
    const data = JSON.parse(stored);
    if (data.date !== today) {
        // Reset for new day
        return { date: today, count: 0 };
    }
    return data;
}

function incrementUsage() {
    const today = new Date().toDateString();
    const usage = getDailyUsage();
    usage.count += 1;
    usage.date = today;
    localStorage.setItem('ais-usage', JSON.stringify(usage));
    return usage.count;
}

function remainingAnalyses() {
    return Math.max(0, DAILY_LIMIT - getDailyUsage().count);
}

// ===== INITIALIZATION =====
document.addEventListener('DOMContentLoaded', function () {
    const tickerInput = document.getElementById('ticker');
    const runButton = document.getElementById('run');
    const refreshButton = document.getElementById('refreshPicks');

    // Content generator
    const contentTickerInput = document.getElementById('contentTicker');
    const generateContentButton = document.getElementById('generateContent');

    // Modal controls
    document.getElementById('closeModal').addEventListener('click', closeUpgradeModal);
    document.getElementById('closeShare').addEventListener('click', closeShareModal);

    // Share button controls
    document.getElementById('shareBtn').addEventListener('click', openShareModal);
    document.getElementById('copyBtn').addEventListener('click', copyAnalysis);

    // Content generator controls
    generateContentButton.addEventListener('click', generateContent);
    contentTickerInput.addEventListener('input', function () {
        this.value = this.value.toUpperCase();
    });

    // Tab switching for content
    document.querySelectorAll('.tab-btn').forEach(btn => {
        btn.addEventListener('click', function() {
            const tab = this.getAttribute('data-tab');
            switchContentTab(tab);
        });
    });

    // Share modal actions
    document.getElementById('shareTwitter').addEventListener('click', shareTwitter);
    document.getElementById('shareCopy').addEventListener('click', shareCopyLink);

    // Click outside modal to close
    document.getElementById('upgradeModal').addEventListener('click', function(e) {
        if (e.target === this) closeUpgradeModal();
    });
    document.getElementById('shareModal').addEventListener('click', function(e) {
        if (e.target === this) closeShareModal();
    });

    // Form inputs
    tickerInput.addEventListener('input', function () {
        this.value = this.value.toUpperCase();
    });

    runButton.addEventListener('click', async function () {
        const ticker = tickerInput.value.trim();
        if (!ticker) {
            setStatus('Enter a ticker symbol to analyze.', 'warning');
            return;
        }
        
        // Check limit
        if (getDailyUsage().count >= DAILY_LIMIT) {
            setStatus('Daily limit reached. Upgrade for unlimited.', 'warning');
            openUpgradeModal();
            return;
        }
        
        await analyzeTicker(ticker);
    });

    refreshButton.addEventListener('click', loadDailyPicks);

    const backtestTicker = document.getElementById('backtestTicker');
    const backtestStart = document.getElementById('backtestStart');
    const backtestEnd = document.getElementById('backtestEnd');
    const backtestSize = document.getElementById('backtestSize');
    const backtestButton = document.getElementById('runBacktest');

    if (backtestButton) {
        backtestButton.addEventListener('click', async function () {
            const ticker = backtestTicker?.value.trim().toUpperCase();
            const startDate = backtestStart?.value;
            const endDate = backtestEnd?.value;
            const size = parseFloat(backtestSize?.value) || 0.02;

            if (!ticker) {
                setStatus('Enter a ticker symbol to backtest.', 'warning');
                return;
            }

            await runBacktest({ ticker, start_date: startDate, end_date: endDate, position_size_pct: size });
        });
    }

    // Load homepage content with Acquisition Agent
    loadHomepageContent();

    loadDailyPicks();
});

async function loadHomepageContent() {
    try {
        const response = await fetch('/api/agent/landing');
        if (response.ok) {
            const data = await response.json();
            const result = data.result;

            // Update hero headline if provided
            if (result.hero_headline) {
                const headlineElement = document.querySelector('.hero-left h1');
                if (headlineElement) {
                    headlineElement.textContent = result.hero_headline;
                }
            }

            // Update hero subheadline if provided
            if (result.hero_subheadline) {
                const subheadlineElement = document.querySelector('.hero-left p');
                if (subheadlineElement) {
                    subheadlineElement.textContent = result.hero_subheadline;
                }
            }

            // Update CTA text if provided
            if (result.cta_text) {
                const ctaButton = document.querySelector('.btn-analyze');
                if (ctaButton) {
                    ctaButton.textContent = result.cta_text;
                }
            }

            // Update ticker suggestions if provided
            if (result.ticker_suggestions && result.ticker_suggestions.length > 0) {
                updateTickerSuggestions(result.ticker_suggestions);
            }
        }
    } catch (error) {
        console.error('Acquisition agent error:', error);
        // Continue with default homepage content
    }
}

function updateTickerSuggestions(suggestions) {
    // Update placeholder text or add suggestions to input
    const tickerInput = document.getElementById('ticker');
    if (tickerInput && suggestions.length > 0) {
        const placeholder = `e.g., ${suggestions.slice(0, 3).map(s => s.ticker).join(', ')}…`;
        tickerInput.placeholder = placeholder;
    }
}

// ===== CORE FUNCTIONS =====
function setStatus(message, type = 'info') {
    const status = document.getElementById('status');
    status.textContent = message;
    status.className = `status ${type}`;
}

async function analyzeTicker(ticker) {
    try {
        setStatus(`Analyzing ${ticker}…`, 'info');
        const result = await analyzeStock(ticker);
        
        // Track usage
        const count = incrementUsage();
        
        // Render the large signal hero
        renderSignalHero(result);
        
        // Store for sharing
        currentAnalysis = result;
        
        setStatus(`Analysis complete. ${remainingAnalyses()} free analyses left today.`, 'success');
        
        // If limit hit after this, show paywall on next attempt
    } catch (error) {
        setStatus(error.message || 'Analysis failed.', 'error');
    }
}

async function renderSignalHero(data) {
    const analysis = data || {};
    const tech = analysis.technical_indicators || {};
    const rec = (analysis.recommendation || 'HOLD').toUpperCase();
    const confidence = analysis.confidence_score || 0;

    // Show hero section
    const heroSection = document.getElementById('signalHero');
    heroSection.style.display = 'block';

    // Call Signal Analyst Agent for enhanced explanations
    try {
        const agentResponse = await fetch('/api/agent/signal', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                context: {
                    raw_analysis: analysis,
                    user_context: {
                        used_today: getDailyUsage().count,
                        remaining_free: remainingAnalyses()
                    }
                }
            })
        });

        if (agentResponse.ok) {
            const agentData = await agentResponse.json();
            const agentResult = agentData.result;

            // Use agent-enhanced content
            document.getElementById('signalTickerLarge').textContent = analysis.ticker || '—';
            document.getElementById('signalRecLarge').textContent = agentResult.ui_payload.recommendation_badge;
            document.getElementById('signalRecLarge').className = `signal-recommendation ${agentResult.ui_payload.recommendation_badge.toLowerCase()}`;

            // Update confidence
            document.getElementById('confidenceFillLarge').style.width = agentResult.ui_payload.confidence_percentage + '%';
            document.getElementById('confidenceValueLarge').textContent = agentResult.ui_payload.confidence_percentage + '%';

            // Update trade details with REAL agent values
            const tradeDetails = agentResult.ui_payload.entry_target_stop;
            const entryPrice = tradeDetails.entry || 0;
            const targetPrice = tradeDetails.target || 0;
            const stopPrice = tradeDetails.stop || 0;
            const upside = targetPrice > entryPrice ? ((targetPrice - entryPrice) / entryPrice * 100).toFixed(1) : 0;

            document.getElementById('entryPriceLarge').textContent = entryPrice ? `$${entryPrice.toFixed(2)}` : '—';
            document.getElementById('targetPriceLarge').textContent = targetPrice ? `$${targetPrice.toFixed(2)}` : '—';
            document.getElementById('stopLossLarge').textContent = stopPrice ? `$${stopPrice.toFixed(2)}` : '—';
            document.getElementById('upsideLarge').textContent = upside ? `+${upside}%` : '—';

            const riskLevel = agentResult.ui_payload.risk_badge;
            document.getElementById('riskLevelLarge').innerHTML = `<span class="risk-badge ${riskLevel.toLowerCase()}">${riskLevel}</span>`;

            const expectedReturn = analysis.expected_return != null ? `${analysis.expected_return > 0 ? '+' : ''}${analysis.expected_return.toFixed(1)}%` : '—';
            document.getElementById('expectedReturnLarge').textContent = expectedReturn;

            // Use agent-generated explanation
            document.getElementById('explanationLarge').textContent = agentResult.why_this_trade || analysis.simple_explanation || 'AI analysis based on technical and fundamental indicators.';

            // ========== NEW: POPULATE AGENT SECTIONS ==========

            // A) SIGNAL HEADLINE
            if (agentResult.signal_summary) {
                const headlineDiv = document.getElementById('signalHeadline');
                headlineDiv.querySelector('.headline-text').textContent = agentResult.signal_summary;
                headlineDiv.style.display = 'block';
            }

            // B) WHY THIS TRADE
            if (agentResult.why_this_trade) {
                const whyDiv = document.getElementById('whyTrade');
                whyDiv.querySelector('.why-trade-text').textContent = agentResult.why_this_trade;
                whyDiv.style.display = 'block';
            }

            // C) RISK ASSESSMENT
            if (agentResult.risk_assessment) {
                const riskDiv = document.getElementById('riskSection');
                riskDiv.querySelector('.risk-assessment-text').textContent = agentResult.risk_assessment;
                riskDiv.style.display = 'block';
            }

            // ========== END NEW SECTIONS ==========

            // Update trust summary with agent content
            renderTrustSummary(agentResult.confidence_explanation || confidence);

            // Show similar opportunities if available
            if (agentResult.similar_opportunities && agentResult.similar_opportunities.length > 0) {
                renderSimilarOpportunities(agentResult.similar_opportunities);
            }

            // LOG FINAL APPLIED VALUES
            console.log('✅ FINAL UI:', {
                ticker: analysis.ticker,
                recommendation: agentResult.ui_payload.recommendation_badge,
                confidence: agentResult.ui_payload.confidence_percentage,
                entry: entryPrice,
                target: targetPrice,
                stop: stopPrice,
                upside: upside,
                headline: agentResult.signal_summary,
                whyTrade: agentResult.why_this_trade,
                riskAssessment: agentResult.risk_assessment
            });

        } else {
            // Fallback to original rendering
            renderSignalHeroFallback(analysis, rec, confidence);
        }
    } catch (error) {
        console.error('Signal Analyst Agent error:', error);
        // Fallback to original rendering
        renderSignalHeroFallback(analysis, rec, confidence);
    }

    // Show metrics section
    document.getElementById('metricsSection').style.display = 'block';
    renderMetrics(analysis);

    // Scroll to signal hero
    heroSection.scrollIntoView({ behavior: 'smooth', block: 'start' });
}

function renderSignalHeroFallback(analysis, rec, confidence) {
    // Original rendering logic as fallback (no agent data available)
    document.getElementById('signalTickerLarge').textContent = analysis.ticker || '—';
    document.getElementById('signalRecLarge').textContent = rec;
    document.getElementById('signalRecLarge').className = `signal-recommendation ${rec.toLowerCase()}`;

    document.getElementById('confidenceFillLarge').style.width = confidence + '%';
    document.getElementById('confidenceValueLarge').textContent = confidence + '%';

    const entryPrice = analysis.entry_price || 0;
    const targetPrice = (entryPrice * 1.1) || 0;
    const stopLoss = (entryPrice * 0.95) || 0;
    const upside = targetPrice > entryPrice ? ((targetPrice - entryPrice) / entryPrice * 100).toFixed(1) : 0;

    document.getElementById('entryPriceLarge').textContent = entryPrice ? `$${entryPrice.toFixed(2)}` : '—';
    document.getElementById('targetPriceLarge').textContent = targetPrice ? `$${targetPrice.toFixed(2)}` : '—';
    document.getElementById('stopLossLarge').textContent = stopLoss ? `$${stopLoss.toFixed(2)}` : '—';
    document.getElementById('upsideLarge').textContent = upside ? `+${upside}%` : '—';

    const riskLevel = analysis.risk_level || 'Medium';
    document.getElementById('riskLevelLarge').innerHTML = `<span class="risk-badge ${riskLevel.toLowerCase()}">${riskLevel}</span>`;

    const expectedReturn = analysis.expected_return != null ? `${analysis.expected_return > 0 ? '+' : ''}${analysis.expected_return.toFixed(1)}%` : '—';
    document.getElementById('expectedReturnLarge').textContent = expectedReturn;

    document.getElementById('explanationLarge').textContent =
        analysis.simple_explanation || analysis.reasoning || 'AI analysis based on technical and fundamental indicators.';

    renderTrustSummary(confidence);

    console.log('⚠️  FALLBACK UI (agent unavailable):', {
        ticker: analysis.ticker,
        recommendation: rec,
        confidence: confidence,
        entry: entryPrice,
        target: targetPrice,
        stop: stopLoss
    });
}

function renderSimilarOpportunities(opportunities) {
    // Add similar opportunities to the UI (placeholder for now)
    const explanationDiv = document.getElementById('explanationLarge');
    if (opportunities.length > 0) {
        let similarText = '\n\nSimilar opportunities: ';
        similarText += opportunities.map(opp => `${opp.ticker} (${opp.confidence}% confidence)`).join(', ');
        explanationDiv.textContent += similarText;
    }
}

function renderTrustSummary(confidence) {
    const summary = document.getElementById('trustSummary');
    if (!summary) return;

    let message = 'This signal is generated from technical and sentiment data.';
    let tone = 'trust-neutral';

    // Handle both numeric confidence and agent-generated explanation
    if (typeof confidence === 'string') {
        // Agent provided explanation
        message = confidence;
        tone = 'trust-medium'; // Default tone for agent explanations
    } else if (typeof confidence === 'number') {
        // Numeric confidence score
        if (confidence >= 75) {
            message = 'High-confidence signal: models are aligned and historical patterns are strong.';
            tone = 'trust-high';
        } else if (confidence >= 50) {
            message = 'Moderate-confidence signal: use this as a directional edge while tracking risk.';
            tone = 'trust-medium';
        } else {
            message = 'Low-confidence signal: treat this as a watchlist idea, not a full trade.';
            tone = 'trust-low';
        }
    }

    summary.textContent = message;
    summary.className = `trust-summary ${tone}`;
}

function renderMetrics(analysis) {
    const tech = analysis.technical_indicators || {};
    const risk = analysis.risk_metrics || {};

    document.getElementById('price').textContent = tech.current_price != null ? `$${tech.current_price}` : '—';
    document.getElementById('rsi').textContent = tech.rsi_14 != null ? tech.rsi_14.toFixed(1) : '—';
    document.getElementById('trend').textContent = tech.trend || '—';
    document.getElementById('vol').textContent = risk.volatility != null ? (risk.volatility * 100).toFixed(1) + '%' : '—';
    document.getElementById('sharpe').textContent = risk.sharpe_ratio != null ? risk.sharpe_ratio.toFixed(2) : '—';
    document.getElementById('cdd').textContent = risk.current_drawdown != null ? (risk.current_drawdown * 100).toFixed(1) + '%' : '—';
    document.getElementById('tickerChip').textContent = analysis.ticker || '—';

    document.getElementById('winRateLarge').textContent = analysis.win_rate != null ? `${(analysis.win_rate * 100).toFixed(1)}%` : '—';
    document.getElementById('avgReturnLarge').textContent = analysis.avg_return != null ? `${analysis.avg_return.toFixed(1)}%` : '—';
    document.getElementById('maxDrawdownLarge').textContent = analysis.max_drawdown != null ? `${(analysis.max_drawdown * 100).toFixed(1)}%` : '—';

    const driversList = document.getElementById('drivers');
    driversList.innerHTML = '';
    (analysis.key_drivers || []).slice(0, 5).forEach(driver => {
        const item = document.createElement('li');
        item.textContent = driver;
        driversList.appendChild(item);
    });
    if (!analysis.key_drivers || !analysis.key_drivers.length) {
        driversList.innerHTML = '<li>Strong technical factors driving this signal</li>';
    }

    document.getElementById('rawJson').textContent = JSON.stringify(analysis, null, 2);

    // Load transparency data using Trust & Proof Agent
    loadTransparencyData();
}

async function loadTransparencyData() {
    try {
        const response = await fetch('/api/agent/transparency');
        if (response.ok) {
            const data = await response.json();
            const result = data.result;

            // Update performance cards if available
            if (result.ui_payload && result.ui_payload.performance_cards) {
                updatePerformanceCards(result.ui_payload.performance_cards);
            }

            // Update last result if available
            if (result.last_signal_result) {
                updateLastSignalResult(result.last_signal_result);
            }
        }
    } catch (error) {
        console.error('Transparency agent error:', error);
        // Continue without transparency data
    }
}

function updatePerformanceCards(cards) {
    // Update existing performance snapshot cards with agent data
    cards.forEach(card => {
        const elementId = card.title.toLowerCase().replace(' ', '');
        const valueElement = document.getElementById(elementId + 'Large');
        if (valueElement && card.value) {
            valueElement.textContent = card.value;
        }
    });
}

function updateLastSignalResult(lastResult) {
    // Could add a "Last Signal Result" section to show historical performance
    // For now, this is a placeholder for future UI enhancement
    console.log('Last signal result:', lastResult);
}

async function analyzeStock(symbol) {
    try {
        const response = await fetch('/api/analyze', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ ticker: symbol })
        });

        if (!response.ok) {
            const body = await response.text();
            throw new Error(`Analysis failed: ${body}`);
        }

        return await response.json();
    } catch (error) {
        console.error('API Error:', error);
        throw error;
    }
}

async function loadDailyPicks() {
    const picksPanel = document.getElementById('topPicksList');
    picksPanel.innerHTML = '<div class="placeholder">Loading top picks…</div>';

    try {
        const response = await fetch('/api/daily-picks');
        if (!response.ok) {
            throw new Error('Daily picks request failed');
        }
        const data = await response.json();
        renderDailyPicks(data.daily_picks || []);
    } catch (error) {
        console.error(error);
        picksPanel.innerHTML = '<div class="placeholder error">Unable to load top picks.</div>';
    }
}

function renderDailyPicks(picks) {
    const picksPanel = document.getElementById('topPicksList');
    picksPanel.innerHTML = '';

    if (!picks.length) {
        picksPanel.innerHTML = '<div class="placeholder">No picks available today.</div>';
        return;
    }

    picks.forEach(pick => {
        const card = document.createElement('div');
        card.className = 'pick-card';
        card.innerHTML = `
            <div class="pick-header">
                <strong>${pick.ticker}</strong>
                <span class="pill small">${pick.risk}</span>
            </div>
            <div class="pick-name">${pick.name}</div>
            <div class="pick-details">
                <span>Confidence: <strong>${pick.confidence}%</strong></span>
                <span>Entry: <strong>$${pick.entry_price}</strong></span>
                <span>Target: <strong>$${pick.target_price}</strong></span>
            </div>
            <p class="pick-reason">${pick.reason}</p>
        `;
        picksPanel.appendChild(card);
    });
}

// ===== MODALS & SHARING =====
function openUpgradeModal() {
    // Fetch personalized conversion content
    loadConversionContent().then(() => {
        document.getElementById('upgradeModal').style.display = 'flex';
    }).catch(() => {
        // Fallback to basic modal
        document.getElementById('upgradeModal').style.display = 'flex';
    });
}

async function loadConversionContent() {
    try {
        const response = await fetch('/api/agent/paywall', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                context: {
                    user_usage: {
                        used_today: getDailyUsage().count,
                        remaining_free: remainingAnalyses()
                    },
                    last_analysis: currentAnalysis,
                    trust_metrics: {
                        win_rate: currentAnalysis?.win_rate || 0,
                        total_signals: currentAnalysis?.total_signals || 0
                    },
                    pricing_state: {
                        price: 14,
                        period: 'month'
                    }
                }
            })
        });

        if (response.ok) {
            const data = await response.json();
            const result = data.result;

            // Update modal content with agent-generated copy
            if (result.upgrade_headline) {
                document.querySelector('#upgradeModal h2').textContent = result.upgrade_headline;
            }

            if (result.value_proposition) {
                const valueElement = document.querySelector('#upgradeModal .modal-body p');
                if (valueElement) {
                    valueElement.textContent = result.value_proposition;
                }
            }

            if (result.social_proof) {
                // Add social proof element if it doesn't exist
                let proofElement = document.querySelector('#upgradeModal .social-proof');
                if (!proofElement) {
                    proofElement = document.createElement('p');
                    proofElement.className = 'social-proof';
                    document.querySelector('#upgradeModal .modal-body').appendChild(proofElement);
                }
                proofElement.textContent = result.social_proof;
            }

            if (result.cta_text) {
                const ctaButton = document.querySelector('#upgradeModal .btn-primary');
                if (ctaButton) {
                    ctaButton.textContent = result.cta_text;
                }
            }

            // Update remaining free signals display
            if (result.ui_payload && result.ui_payload.remaining_free !== undefined) {
                const remainingElement = document.querySelector('#upgradeModal .remaining-free');
                if (remainingElement) {
                    remainingElement.textContent = `${result.ui_payload.remaining_free} free signals remaining`;
                }
            }
        }
    } catch (error) {
        console.error('Conversion agent error:', error);
        // Modal will still open with default content
    }
}

function closeUpgradeModal() {
    document.getElementById('upgradeModal').style.display = 'none';
}

function openShareModal() {
    document.getElementById('shareModal').style.display = 'flex';
}

function closeShareModal() {
    document.getElementById('shareModal').style.display = 'none';
}

function shareTwitter() {
    if (!currentAnalysis) return;
    
    const ticker = currentAnalysis.ticker || '?';
    const signal = currentAnalysis.recommendation || 'HOLD';
    const confidence = currentAnalysis.confidence_score || 0;
    const url = window.location.href;
    
    const text = `🎯 ${ticker} ${signal} | ${confidence}% confidence 
Just got this signal from AI Stock Signals. No financial advice, not a guru tip.
Try it free: `;
    
    window.open(`https://twitter.com/intent/tweet?text=${encodeURIComponent(text)}&url=${encodeURIComponent(url)}`, 'share');
}

function shareCopyLink() {
    const url = window.location.href;
    navigator.clipboard.writeText(url).then(() => {
        alert('Signal link copied to clipboard!');
        closeShareModal();
    });
}

function copyAnalysis() {
    if (!currentAnalysis) return;
    const text = JSON.stringify(currentAnalysis, null, 2);
    navigator.clipboard.writeText(text).then(() => {
        setStatus('Analysis copied to clipboard!', 'success');
    });
}


async function analyzeStock(symbol) {
    try {
        const response = await fetch('/api/analyze', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ ticker: symbol })
        });

        if (!response.ok) {
            const body = await response.text();
            throw new Error(`Analysis failed: ${body}`);
        }

        return await response.json();
    } catch (error) {
        console.error('API Error:', error);
        throw error;
    }
}

async function loadDailyPicks() {
    const picksPanel = document.getElementById('topPicksList');
    picksPanel.innerHTML = '<div class="placeholder">Loading top picks…</div>';

    try {
        const response = await fetch('/api/daily-picks');
        if (!response.ok) {
            throw new Error('Daily picks request failed');
        }
        const data = await response.json();
        renderDailyPicks(data.daily_picks || []);
    } catch (error) {
        console.error(error);
        picksPanel.innerHTML = '<div class="placeholder error">Unable to load top picks.</div>';
    }
}

async function runBacktest(payload) {
    const status = document.getElementById('backtestStatus');
    const resultsSection = document.getElementById('backtestResults');
    if (status) {
        status.textContent = 'Running backtest...';
        status.className = 'status info';
    }
    if (resultsSection) {
        resultsSection.style.display = 'none';
    }

    try {
        const response = await fetch('/api/backtest', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(payload)
        });

        if (!response.ok) {
            const errorText = await response.text();
            throw new Error(errorText || 'Backtest request failed');
        }

        const data = await response.json();
        renderBacktestResults(data);
        if (status) {
            status.textContent = 'Backtest complete.';
            status.className = 'status success';
        }
        if (resultsSection) {
            resultsSection.style.display = 'block';
        }
    } catch (error) {
        console.error('Backtest error:', error);
        if (status) {
            status.textContent = error.message || 'Backtest failed.';
            status.className = 'status error';
        }
        if (resultsSection) {
            resultsSection.style.display = 'none';
        }
    }
}

function renderBacktestResults(data) {
    document.getElementById('btTotalReturn').textContent = `${data.total_return_pct}%`;
    document.getElementById('btSharpe').textContent = data.sharpe_ratio.toFixed(2);
    document.getElementById('btDrawdown').textContent = `${data.max_drawdown_pct}%`;
    document.getElementById('btWinRate').textContent = `${data.win_rate_pct}%`;
    document.getElementById('btTrades').textContent = data.trade_count;

    renderBacktestChart(data.equity_curve);
    renderBacktestTradeLog(data.trades);
}

function renderBacktestChart(curve) {
    const canvas = document.getElementById('backtestChart');
    if (!canvas) return;
    const ctx = canvas.getContext('2d');
    const labels = curve.map(point => point.date);
    const values = curve.map(point => point.equity);

    if (backtestChart) {
        backtestChart.destroy();
    }

    backtestChart = new Chart(ctx, {
        type: 'line',
        data: {
            labels,
            datasets: [{
                label: 'Equity Curve',
                data: values,
                borderColor: '#38bdf8',
                backgroundColor: 'rgba(56, 189, 248, 0.15)',
                fill: true,
                tension: 0.2,
                pointRadius: 0
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            scales: {
                x: {
                    ticks: { maxTicksLimit: 10 }
                },
                y: {
                    ticks: {
                        callback: value => `$${value.toLocaleString()}`
                    }
                }
            },
            plugins: {
                legend: { display: false },
                tooltip: {
                    callbacks: {
                        label: context => `$${context.parsed.y.toFixed(2)}`
                    }
                }
            }
        }
    });
}

function renderBacktestTradeLog(trades) {
    const logContainer = document.getElementById('backtestTradeLog');
    if (!logContainer) return;

    if (!trades || !trades.length) {
        logContainer.innerHTML = '<p class="placeholder">No trades were generated for this period.</p>';
        return;
    }

    const rows = trades.map(trade => `
        <tr>
          <td>${trade.entry_date || 'N/A'}</td>
          <td>${trade.exit_date || 'N/A'}</td>
          <td>${trade.entry_price != null ? '$' + trade.entry_price.toFixed(2) : '—'}</td>
          <td>${trade.exit_price != null ? '$' + trade.exit_price.toFixed(2) : '—'}</td>
          <td>${trade.shares || 0}</td>
          <td>${trade.pnl != null ? '$' + trade.pnl.toFixed(2) : '—'}</td>
          <td>${trade.return_pct != null ? trade.return_pct.toFixed(2) + '%' : '—'}</td>
        </tr>
    `).join('');

    logContainer.innerHTML = `
      <div class="table-responsive">
        <table class="table table-sm table-striped">
          <thead>
            <tr>
              <th>Entry</th>
              <th>Exit</th>
              <th>Entry Price</th>
              <th>Exit Price</th>
              <th>Shares</th>
              <th>PnL</th>
              <th>Return</th>
            </tr>
          </thead>
          <tbody>
            ${rows}
          </tbody>
        </table>
      </div>
    `;
}

function renderDailyPicks(picks) {
    try {
        const response = await fetch('/api/health');
        return await response.json();
    } catch (error) {
        console.error('Health check failed:', error);
        return null;
    }
}

// ===== CONTENT GENERATION =====
async function generateContent() {
    const ticker = document.getElementById('contentTicker').value.trim();
    if (!ticker) {
        setContentStatus('Enter a ticker symbol to generate content.', 'warning');
        return;
    }

    try {
        setContentStatus('Generating viral content…', 'info');
        const response = await fetch('/api/generate-content', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ ticker: ticker })
        });

        if (!response.ok) {
            const body = await response.text();
            throw new Error(`Content generation failed: ${body}`);
        }

        const data = await response.json();
        
        // Populate the content areas
        document.getElementById('twitterPost').value = data.twitter_post;
        document.getElementById('redditPost').value = data.reddit_post;
        document.getElementById('tiktokScript').value = data.tiktok_script;
        
        // Show the output
        document.getElementById('contentOutput').style.display = 'block';
        
        setContentStatus('Content generated! Copy and post.', 'success');
        
    } catch (error) {
        setContentStatus(error.message || 'Content generation failed.', 'error');
    }
}

function setContentStatus(message, type = 'info') {
    const status = document.getElementById('contentStatus');
    status.textContent = message;
    status.className = `status ${type}`;
}

function switchContentTab(tab) {
    // Hide all tabs
    document.querySelectorAll('.tab-pane').forEach(pane => {
        pane.classList.remove('active');
    });
    document.querySelectorAll('.tab-btn').forEach(btn => {
        btn.classList.remove('active');
    });
    
    // Show selected tab
    document.getElementById(tab + 'Tab').classList.add('active');
    document.querySelector(`[data-tab="${tab}"]`).classList.add('active');
}

function copyToClipboard(elementId) {
    const element = document.getElementById(elementId);
    element.select();
    document.execCommand('copy');
    setContentStatus('Copied to clipboard!', 'success');
}

// Export functions
window.FinancialIntelligence = {
    analyzeStock,
    checkSystemHealth,
    generateContent
};