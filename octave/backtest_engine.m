% backtest_engine.m
% Vectorized Backtesting Engine for AI Stock Agent Strategy
% Implements Core-Satellite scoring with no look-ahead bias

function results = backtest_engine(data_file, stock_type, params)
    % Load data from MAT file
    % data_file: path to .mat file with OHLCV data
    % stock_type: 'Core' or 'Satellite'
    % params: struct with strategy parameters (optional)
    
    fprintf('🚀 Loading data from: %s\n', data_file);
    load(data_file);
    
    % Set default parameters if not provided
    if nargin < 3
        params = struct();
    end
    
    % Default strategy parameters
    if ~isfield(params, 'rsi_period'), params.rsi_period = 14; end
    if ~isfield(params, 'rsi_oversold'), params.rsi_oversold = 30; end
    if ~isfield(params, 'ma_short'), params.ma_short = 50; end
    if ~isfield(params, 'ma_long'), params.ma_long = 200; end
    if ~isfield(params, 'dual_momentum_period'), params.dual_momentum_period = 252; end
    
    % Strategy thresholds (from config.yaml)
    if strcmp(stock_type, 'Core')
        params.threshold_buy = 60;
        params.threshold_sell = 35;
    else  % Satellite
        params.threshold_buy = 70;
        params.threshold_sell = 40;
    end
    
    fprintf('📊 Data loaded: %d bars (%s to %s)\n', ...
            length(close), datestr(dates(1)), datestr(dates(end)));
    fprintf('Strategy type: %s\n\n', stock_type);
    
    % ========== INDICATOR CALCULATION (Vectorized) ==========
    
    % 1. RSI Calculation
    fprintf('Calculating RSI...\n');
    rsi = calculate_rsi_vectorized(close, params.rsi_period);
    
    % 2. Moving Averages
    fprintf('Calculating Moving Averages...\n');
    ma200 = movavg(close, params.ma_long, params.ma_long, 0);
    
    % 3. Dual Momentum (12-month return)
    fprintf('Calculating Dual Momentum...\n');
    returns_12m = zeros(size(close));
    for i = params.dual_momentum_period+1:length(close)
        returns_12m(i) = (close(i) - close(i-params.dual_momentum_period)) / close(i-params.dual_momentum_period);
    end
    dual_momentum = returns_12m > 0;  % Bullish if positive 12-month return
    
    % 4. Bollinger Bands (for oversold detection)
    fprintf('Calculating Bollinger Bands...\n');
    [bb_upper, bb_lower] = calculate_bollinger(close, 20, 2);
    is_oversold_bb = close < bb_lower;
    
    % ========== SIGNAL GENERATION ==========
    
    fprintf('\n🎯 Generating trading signals...\n');
    
    % Market regime (simplified: price > MA200)
    market_bullish = close > ma200;
    
    % Initialize score components
    n = length(close);
    confidence_score = zeros(n, 1);
    
    if strcmp(stock_type, 'Core')
        % === CORE STRATEGY ===
        % Weights: market=10%, quality=60%, cost=20%, sentiment=10%
        
        % Market filter (10%)
        market_score = market_bullish * 10;
        
        % Quality (60%) - Dual momentum
        quality_score = dual_momentum * 60;
        
        % Cost timing (20%) - Buy when oversold
        cost_score = is_oversold_bb * 20;
        
        % Sentiment (10%) - neutral placeholder
        sentiment_score = ones(n, 1) * 5;
        
        confidence_score = market_score + quality_score + cost_score + sentiment_score;
        
    else
        % === SATELLITE STRATEGY ===
        % Weights: market=25%, quality=35%, technical=30%, sentiment=10%
        
        % Market filter (25%)
        market_score = market_bullish * 25;
        
        % Quality (35%) - Dual momentum
        quality_score = dual_momentum * 35;
        
        % Technical (30%) - RSI oversold
        technical_score = zeros(n, 1);
        technical_score(rsi < 30) = 30;
        technical_score(rsi >= 30 & rsi < 35) = 20;
        technical_score(rsi >= 35 & rsi < 40) = 10;
        
        % Sentiment (10%) - neutral placeholder
        sentiment_score = ones(n, 1) * 5;
        
        confidence_score = market_score + quality_score + technical_score + sentiment_score;
    end
    
    % Generate discrete signals
    signal = zeros(n, 1);  % 0 = no position
    signal(confidence_score >= params.threshold_buy) = 1;  % 1 = long position
    
    % ========== AVOID LOOK-AHEAD BIAS ==========
    % Signal at time t can only be acted upon at time t+1
    % Shift signal forward by 1 period
    position = [0; signal(1:end-1)];
    
    fprintf('Total signals generated: %d BUY signals\n', sum(signal == 1));
    
    % ========== RETURNS CALCULATION ==========
    
    fprintf('\n💰 Calculating returns...\n');
    
    % Asset returns (log returns for better compounding)
    asset_returns = [0; diff(log(close))];
    
    % Strategy returns = position * asset returns
    strategy_returns = position .* asset_returns;
    
    % Equity curves
    equity_strategy = cumprod(1 + strategy_returns);
    equity_buyhold = cumprod(1 + asset_returns);
    
    % ========== PERFORMANCE METRICS ==========
    
    fprintf('\n📈 Calculating performance metrics...\n');
    
    % Total returns
    total_return_strategy = (equity_strategy(end) - 1) * 100;
    total_return_buyhold = (equity_buyhold(end) - 1) * 100;
    
    % Annualized returns (assuming 252 trading days per year)
    n_years = length(close) / 252;
    cagr_strategy = (equity_strategy(end)^(1/n_years) - 1) * 100;
    cagr_buyhold = (equity_buyhold(end)^(1/n_years) - 1) * 100;
    
    % Sharpe Ratio (annualized, assuming Rf=0)
    sharpe_strategy = (mean(strategy_returns) / std(strategy_returns)) * sqrt(252);
    sharpe_buyhold = (mean(asset_returns) / std(asset_returns)) * sqrt(252);
    
    % Maximum Drawdown
    max_dd_strategy = calculate_max_drawdown(equity_strategy);
    max_dd_buyhold = calculate_max_drawdown(equity_buyhold);
    
    % Win rate
    winning_days = sum(strategy_returns(position == 1) > 0);
    total_days_invested = sum(position == 1);
    win_rate = (winning_days / total_days_invested) * 100;
    
    % ========== RESULTS OUTPUT ==========
    
    fprintf('\n============================================================\n');
    fprintf('BACKTEST RESULTS (%s Strategy)\n', stock_type);
    fprintf('============================================================\n\n');
    
    fprintf('Period: %s to %s (%.1f years)\n', ...
            datestr(dates(1)), datestr(dates(end)), n_years);
    fprintf('Starting Price: $%.2f | Ending Price: $%.2f\n\n', close(1), close(end));
    
    fprintf('STRATEGY PERFORMANCE:\n');
    fprintf('  Total Return:    %+.2f%%\n', total_return_strategy);
    fprintf('  CAGR:            %+.2f%%\n', cagr_strategy);
    fprintf('  Sharpe Ratio:    %.3f\n', sharpe_strategy);
    fprintf('  Max Drawdown:    %.2f%%\n', max_dd_strategy);
    fprintf('  Win Rate:        %.1f%%\n', win_rate);
    fprintf('  Days Invested:   %d / %d (%.1f%%)\n\n', ...
            total_days_invested, length(close), (total_days_invested/length(close))*100);
    
    fprintf('BUY & HOLD BENCHMARK:\n');
    fprintf('  Total Return:    %+.2f%%\n', total_return_buyhold);
    fprintf('  CAGR:            %+.2f%%\n', cagr_buyhold);
    fprintf('  Sharpe Ratio:    %.3f\n', sharpe_buyhold);
    fprintf('  Max Drawdown:    %.2f%%\n\n', max_dd_buyhold);
    
    fprintf('OUTPERFORMANCE:\n');
    fprintf('  Alpha:           %+.2f%%\n', total_return_strategy - total_return_buyhold);
    fprintf('  CAGR Diff:       %+.2f%%\n\n', cagr_strategy - cagr_buyhold);
    
    fprintf('============================================================\n');
    
    % Package results
    results = struct();
    results.symbol = symbol;
    results.stock_type = stock_type;
    results.dates = dates;
    results.close = close;
    results.signals = signal;
    results.positions = position;
    results.confidence_scores = confidence_score;
    results.equity_strategy = equity_strategy;
    results.equity_buyhold = equity_buyhold;
    results.total_return = total_return_strategy;
    results.cagr = cagr_strategy;
    results.sharpe = sharpe_strategy;
    results.max_drawdown = max_dd_strategy;
    results.win_rate = win_rate;
    results.alpha = total_return_strategy - total_return_buyhold;
    
    % Save results
    output_file = strrep(data_file, '_data.mat', sprintf('_backtest_%s.mat', stock_type));
    save(output_file, 'results');
    fprintf('\n✅ Results saved to: %s\n', output_file);
end


% ========== HELPER FUNCTIONS ==========

function rsi = calculate_rsi_vectorized(prices, period)
    % Vectorized RSI calculation
    delta = [0; diff(prices)];
    gain = max(delta, 0);
    loss = max(-delta, 0);
    
    % Initial average gain/loss (SMA)
    avg_gain = movavg(gain, period, period, 0);
    avg_loss = movavg(loss, period, period, 0);
    
    % RS and RSI
    rs = avg_gain ./ (avg_loss + 1e-10);  % Add epsilon to avoid division by zero
    rsi = 100 - (100 ./ (1 + rs));
    
    % First 'period' values are NaN, set to 50 (neutral)
    rsi(1:period) = 50;
end


function [upper, lower] = calculate_bollinger(prices, period, num_std)
    % Bollinger Bands calculation
    ma = movavg(prices, period, period, 0);
    
    % Vectorized standard deviation calculation
    stdev = zeros(size(prices));
    for i = period:length(prices)
        stdev(i) = std(prices(i-period+1:i));
    end
    
    upper = ma + (num_std * stdev);
    lower = ma - (num_std * stdev);
end


function max_dd = calculate_max_drawdown(equity_curve)
    % Maximum Drawdown calculation
    running_max = cummax(equity_curve);
    drawdown = (equity_curve - running_max) ./ running_max * 100;
    max_dd = abs(min(drawdown));
end


function ma = movavg(data, lead, lag, alpha)
    % Simple wrapper for moving average
    % For SMA: lead=lag, alpha=0
    n = length(data);
    ma = zeros(n, 1);
    
    for i = lag:n
        ma(i) = mean(data(i-lag+1:i));
    end
    
    % Fill initial values with first valid value
    ma(1:lag-1) = ma(lag);
end
