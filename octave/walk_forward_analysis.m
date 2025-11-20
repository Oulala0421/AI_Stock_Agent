% walk_forward_analysis.m
% Walk-Forward Analysis for Out-of-Sample Parameter Validation
% Prevents overfitting by simulating real-world parameter optimization

function wfa_results = walk_forward_analysis(data_file, stock_type, config)
    % Perform Walk-Forward Analysis
    % data_file: path to .mat file with OHLCV data
    % stock_type: 'Core' or 'Satellite'
    % config: struct with WFA configuration (optional)
    
    fprintf('\n============================================================\n');
    fprintf('WALK-FORWARD ANALYSIS\n');
    fprintf('============================================================\n\n');
    
    % Load data
    load(data_file);
    n_days = length(close);
    
    % Default configuration
    if nargin < 3
        config = struct();
    end
    
    % WFA windows (in trading days, ~252 per year)
    if ~isfield(config, 'is_window'), config.is_window = 504; end  % 2 years
    if ~isfield(config, 'oos_window'), config.oos_window = 126; end  % 6 months
    if ~isfield(config, 'step_size'), config.step_size = 126; end  % Move forward 6 months each time
    
    % Parameter grid to test
    if ~isfield(config, 'rsi_thresholds'), config.rsi_thresholds = [30, 35, 40]; end
    if ~isfield(config, 'buy_thresholds')
        if strcmp(stock_type, 'Core')
            config.buy_thresholds = [55, 60, 65];
        else
            config.buy_thresholds = [65, 70, 75];
        end
    end
    
    fprintf('Configuration:\n');
    fprintf('  In-Sample Window:  %d days (~%.1f years)\n', config.is_window, config.is_window/252);
    fprintf('  Out-of-Sample:     %d days (~%.1f years)\n', config.oos_window, config.oos_window/252);
    fprintf('  Step Size:         %d days\n', config.step_size);
    fprintf('  RSI Thresholds:    [%s]\n', num2str(config.rsi_thresholds));
    fprintf('  Buy Thresholds:    [%s]\n\n', num2str(config.buy_thresholds));
    
    % Calculate number of WFA iterations
    total_window = config.is_window + config.oos_window;
    n_iterations = floor((n_days - total_window) / config.step_size) + 1;
    
    fprintf('Total data points: %d days\n', n_days);
    fprintf('WFA iterations:    %d\n\n', n_iterations);
    
    if n_iterations < 2
        error('Not enough data for Walk-Forward Analysis. Need at least %d days.', total_window + config.step_size);
    end
    
    % Storage for results
    wfa_results = struct();
    wfa_results.dates_oos = {};
    wfa_results.returns_oos = [];
    wfa_results.best_params = {};
    wfa_results.is_performance = [];
    wfa_results.oos_performance = [];
    
    % ========== WFA ITERATIONS ==========
    
    for iter = 1:n_iterations
        fprintf('------------------------------------------------------------\n');
        fprintf('Iteration %d/%d\n', iter, n_iterations);
        fprintf('------------------------------------------------------------\n');
        
        % Define windows
        start_idx = (iter - 1) * config.step_size + 1;
        is_end = start_idx + config.is_window - 1;
        oos_start = is_end + 1;
        oos_end = min(oos_start + config.oos_window - 1, n_days);
        
        if oos_end <= oos_start
            fprintf('Skipping: insufficient OOS data\n');
            break;
        end
        
        fprintf('IS Period:  %s to %s (%d days)\n', ...
                datestr(dates(start_idx)), datestr(dates(is_end)), is_end - start_idx + 1);
        fprintf('OOS Period: %s to %s (%d days)\n\n', ...
                datestr(dates(oos_start)), datestr(dates(oos_end)), oos_end - oos_start + 1);
        
        % Extract IS data
        is_data = struct();
        is_data.close = close(start_idx:is_end);
        is_data.dates = dates(start_idx:is_end);
        
        % ========== IN-SAMPLE OPTIMIZATION ==========
        fprintf('Optimizing parameters on IS data...\n');
        
        best_sharpe = -inf;
        best_params = struct();
        
        % Grid search
        for rsi_thresh = config.rsi_thresholds
            for buy_thresh = config.buy_thresholds
                % Create parameter set
                params = struct();
                params.rsi_oversold = rsi_thresh;
                params.threshold_buy = buy_thresh;
                params.rsi_period = 14;
                params.ma_long = 200;
                params.dual_momentum_period = 252;
                
                % Run backtest on IS period
                perf = run_simple_backtest(is_data, stock_type, params);
                
                % Track best parameters
                if perf.sharpe > best_sharpe
                    best_sharpe = perf.sharpe;
                    best_params = params;
                    best_is_return = perf.total_return;
                end
            end
        end
        
        fprintf('Best IS params: RSI=%d, BuyThresh=%d (Sharpe=%.3f, Return=%.2f%%)\n', ...
                best_params.rsi_oversold, best_params.threshold_buy, best_sharpe, best_is_return);
        
        % ========== OUT-OF-SAMPLE VALIDATION ==========
        fprintf('Testing on OOS data...\n');
        
        % Extract OOS data
        oos_data = struct();
        oos_data.close = close(oos_start:oos_end);
        oos_data.dates = dates(oos_start:oos_end);
        
        % Run backtest with best IS parameters on OOS data
        oos_perf = run_simple_backtest(oos_data, stock_type, best_params);
        
        fprintf('OOS Performance: Return=%.2f%%, Sharpe=%.3f\n', ...
                oos_perf.total_return, oos_perf.sharpe);
        fprintf('Degradation: %.1f%% (IS %.2f%% -> OOS %.2f%%)\n\n', ...
                ((oos_perf.total_return / best_is_return) - 1) * 100, ...
                best_is_return, oos_perf.total_return);
        
        % Store results
        wfa_results.dates_oos{iter} = oos_data.dates;
        wfa_results.returns_oos(iter) = oos_perf.total_return;
        wfa_results.best_params{iter} = best_params;
        wfa_results.is_performance(iter) = best_is_return;
        wfa_results.oos_performance(iter) = oos_perf.total_return;
    end
    
    % ========== WFA SUMMARY ==========
    fprintf('\n============================================================\n');
    fprintf('WALK-FORWARD ANALYSIS SUMMARY\n');
    fprintf('============================================================\n\n');
    
    fprintf('Completed Iterations: %d\n\n', length(wfa_results.oos_performance));
    
    fprintf('IN-SAMPLE Performance:\n');
    fprintf('  Mean Return:   %.2f%%\n', mean(wfa_results.is_performance));
    fprintf('  Std Dev:       %.2f%%\n\n', std(wfa_results.is_performance));
    
    fprintf('OUT-OF-SAMPLE Performance:\n');
    fprintf('  Mean Return:   %.2f%%\n', mean(wfa_results.oos_performance));
    fprintf('  Std Dev:       %.2f%%\n\n', std(wfa_results.oos_performance));
    
    % WFA Efficiency Ratio
    wfa_efficiency = mean(wfa_results.oos_performance) / mean(wfa_results.is_performance);
    fprintf('WFA Efficiency Ratio: %.2f (OOS/IS)\n', wfa_efficiency);
    
    if wfa_efficiency > 0.7
        fprintf('  ✅ EXCELLENT: Strategy is robust and stable\n');
    elseif wfa_efficiency > 0.5
        fprintf('  ✅ GOOD: Strategy has acceptable degradation\n');
    elseif wfa_efficiency > 0.3
        fprintf('  ⚠️  MODERATE: Strategy shows significant overfitting\n');
    else
        fprintf('  ❌ POOR: Strategy is severely overfit, NOT recommended\n');
    end
    
    fprintf('\n============================================================\n');
    
    % Save results
    save('walk_forward_results.mat', 'wfa_results');
    fprintf('\n✅ WFA results saved to: walk_forward_results.mat\n');
end


% ===== HELPER FUNCTION: Simplified Backtest =====
function perf = run_simple_backtest(data, stock_type, params)
    % Simplified backtest for parameter optimization
    
    close = data.close;
    n = length(close);
    
    % RSI
    rsi = calculate_rsi(close, params.rsi_period);
    
    % MA200
    ma200 = movavg(close, params.ma_long, params.ma_long, 0);
    market_bullish = close > ma200;
    
    % Dual momentum (12m return)
    returns_12m = zeros(n, 1);
    for i = params.dual_momentum_period+1:n
        returns_12m(i) = (close(i) - close(i-params.dual_momentum_period)) / close(i-params.dual_momentum_period);
    end
    dual_momentum = returns_12m > 0;
    
    % Simple scoring (using only available data)
    score = zeros(n, 1);
    score = score + market_bullish * 30;
    score = score + dual_momentum * 40;
    score(rsi < params.rsi_oversold) = score(rsi < params.rsi_oversold) + 30;
    
    % Generate signals
    signal = score >= params.threshold_buy;
    position = [0; signal(1:end-1)];  % Lag to avoid look-ahead bias
    
    % Returns
    log_returns = [0; diff(log(close))];
    strategy_returns = position .* log_returns;
    
    % Performance metrics
    equity = cumprod(1 + strategy_returns);
    total_return = (equity(end) - 1) * 100;
    sharpe = (mean(strategy_returns) / (std(strategy_returns) + 1e-10)) * sqrt(252);
    
    perf = struct();
    perf.total_return = total_return;
    perf.sharpe = sharpe;
end


function rsi = calculate_rsi(prices, period)
    delta = [0; diff(prices)];
    gain = max(delta, 0);
    loss = max(-delta, 0);
    avg_gain = movavg(gain, period, period, 0);
    avg_loss = movavg(loss, period, period, 0);
    rs = avg_gain ./ (avg_loss + 1e-10);
    rsi = 100 - (100 ./ (1 + rs));
    rsi(1:period) = 50;
end


function ma = movavg(data, lead, lag, alpha)
    n = length(data);
    ma = zeros(n, 1);
    for i = lag:n
        ma(i) = mean(data(i-lag+1:i));
    end
    ma(1:lag-1) = ma(lag);
end
