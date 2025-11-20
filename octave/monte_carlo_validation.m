% monte_carlo_validation.m
% Monte Carlo Simulation for Strategy Robustness Testing
% Implements both trade shuffling and permutation tests

function mc_results = monte_carlo_validation(backtest_results, n_simulations)
    % Run Monte Carlo validation on backtest results
    % backtest_results: output from backtest_engine.m
    % n_simulations: number of Monte Carlo iterations (default 1000)
    
    if nargin < 2
        n_simulations = 1000;
    end
    
    fprintf('\n============================================================\n');
    fprintf('MONTE CARLO SIMULATION - Robustness Validation\n');
    fprintf('============================================================\n\n');
    fprintf('Simulations: %d\n', n_simulations);
    fprintf('Strategy: %s\n\n', backtest_results.stock_type);
    
    % Extract data
    close = backtest_results.close;
    positions = backtest_results.positions;
    actual_return = backtest_results.total_return;
    actual_sharpe = backtest_results.sharpe;
    actual_max_dd = backtest_results.max_drawdown;
    
    % Calculate log returns
    log_returns = [0; diff(log(close))];
    
    % ========== METHOD 1: TRADE SHUFFLING ==========
    fprintf('📊 Method 1: Trade Sequence Shuffling (Bootstrap)\n');
    fprintf('Testing if trade order affects results...\n\n');
    
    % Extract individual trades
    trade_returns = log_returns(positions == 1);
    n_trades = length(trade_returns);
    
    if n_trades < 10
        fprintf('⚠️ Warning: Too few trades (%d) for reliable simulation\n\n', n_trades);
        trade_shuffle_returns = [];
        trade_shuffle_drawdowns = [];
    else
        trade_shuffle_returns = zeros(n_simulations, 1);
        trade_shuffle_drawdowns = zeros(n_simulations, 1);
        
        fprintf('Progress: ');
        for i = 1:n_simulations
            % Randomly shuffle trade sequence (with replacement - bootstrap)
            shuffled_trades = trade_returns(randi(n_trades, n_trades, 1));
            
            % Calculate equity curve from shuffled trades
            equity_shuffled = cumprod(1 + shuffled_trades);
            
            % Metrics
            trade_shuffle_returns(i) = (equity_shuffled(end) - 1) * 100;
            trade_shuffle_drawdowns(i) = calculate_max_drawdown(equity_shuffled);
            
            if mod(i, 100) == 0
                fprintf('%d...', i);
            end
        end
        fprintf('Done!\n\n');
        
        % Statistics
        fprintf('Trade Shuffling Results:\n');
        fprintf('  Original Return:        %.2f%%\n', actual_return);
        fprintf('  Mean Shuffled Return:   %.2f%% (±%.2f%%)\n', ...
                mean(trade_shuffle_returns), std(trade_shuffle_returns));
        fprintf('  Return Percentile:      %.1f%% (higher = better)\n\n', ...
                sum(trade_shuffle_returns < actual_return) / n_simulations * 100);
        
        fprintf('  Original Max DD:        %.2f%%\n', actual_max_dd);
        fprintf('  Mean Shuffled Max DD:   %.2f%% (±%.2f%%)\n', ...
                mean(trade_shuffle_drawdowns), std(trade_shuffle_drawdowns));
        fprintf('  95%% Confidence DD:      %.2f%%\n\n', ...
                prctile(trade_shuffle_drawdowns, 95));
    end
    
    % ========== METHOD 2: PERMUTATION TEST ==========
    fprintf('📊 Method 2: Permutation Test (Return Shuffling)\n');
    fprintf('Testing if strategy has real edge vs randomness...\n\n');
    
    permuted_returns = zeros(n_simulations, 1);
    permuted_sharpes = zeros(n_simulations, 1);
    
    n_days = length(log_returns);
    
    fprintf('Progress: ');
    for i = 1:n_simulations
        % Randomly shuffle the MARKET returns (destroys temporal structure)
        shuffled_indices = randperm(n_days);
        shuffled_market_returns = log_returns(shuffled_indices);
        
        % Apply original strategy positions to shuffled returns
        strategy_returns_permuted = positions .* shuffled_market_returns;
        
        % Calculate performance on randomized data
        equity_permuted = cumprod(1 + strategy_returns_permuted);
        permuted_returns(i) = (equity_permuted(end) - 1) * 100;
        
        % Sharpe ratio
        if sum(positions) > 0
            permuted_sharpes(i) = (mean(strategy_returns_permuted) / std(strategy_returns_permuted)) * sqrt(252);
        else
            permuted_sharpes(i) = 0;
        end
        
        if mod(i, 100) == 0
            fprintf('%d...', i);
        end
    end
    fprintf('Done!\n\n');
    
    % Calculate p-value
    p_value = sum(permuted_returns >= actual_return) / n_simulations;
    p_value_sharpe = sum(permuted_sharpes >= actual_sharpe) / n_simulations;
    
    fprintf('Permutation Test Results:\n');
    fprintf('  Original Return:         %.2f%%\n', actual_return);
    fprintf('  Mean Permuted Return:    %.2f%% (±%.2f%%)\n', ...
            mean(permuted_returns), std(permuted_returns));
    fprintf('  P-value (Return):        %.4f %s\n', p_value, ...
            get_significance_label(p_value));
    fprintf('\n');
    fprintf('  Original Sharpe:         %.3f\n', actual_sharpe);
    fprintf('  Mean Permuted Sharpe:    %.3f (±%.3f)\n', ...
            mean(permuted_sharpes), std(permuted_sharpes));
    fprintf('  P-value (Sharpe):        %.4f %s\n', p_value_sharpe, ...
            get_significance_label(p_value_sharpe));
    fprintf('\n');
    
    % ========== INTERPRETATION ==========
    fprintf('------------------------------------------------------------\n');
    fprintf('🎯 INTERPRETATION:\n');
    fprintf('------------------------------------------------------------\n');
    
    if p_value < 0.01
        fprintf('✅ HIGHLY SIGNIFICANT (p < 0.01)\n');
        fprintf('   Strategy shows VERY STRONG statistical edge.\n');
        fprintf('   Unlikely to be due to random chance.\n');
    elseif p_value < 0.05
        fprintf('✅ SIGNIFICANT (p < 0.05)\n');
        fprintf('   Strategy shows statistical edge.\n');
        fprintf('   Result is meaningful, not just luck.\n');
    elseif p_value < 0.10
        fprintf('⚠️  MARGINALLY SIGNIFICANT (p < 0.10)\n');
        fprintf('   Strategy shows weak edge.\n');
        fprintf('   Consider further validation before live trading.\n');
    else
        fprintf('❌ NOT SIGNIFICANT (p >= 0.10)\n');
        fprintf('   Strategy does NOT show reliable edge.\n');
        fprintf('   Performance may be due to luck/overfitting.\n');
        fprintf('   DO NOT trade this strategy without major improvements.\n');
    end
    
    if ~isempty(trade_shuffle_drawdowns)
        dd_95 = prctile(trade_shuffle_drawdowns, 95);
        fprintf('\n💡 Risk Management:\n');
        fprintf('   95%% Confidence Max Drawdown: %.2f%%\n', dd_95);
        fprintf('   Recommended Capital Buffer: %.2f%% above initial capital\n', dd_95 * 1.5);
    end
    
    fprintf('============================================================\n\n');
    
    % Package results
    mc_results = struct();
    mc_results.n_simulations = n_simulations;
    mc_results.trade_shuffle_returns = trade_shuffle_returns;
    mc_results.trade_shuffle_drawdowns = trade_shuffle_drawdowns;
    mc_results.permuted_returns = permuted_returns;
    mc_results.permuted_sharpes = permuted_sharpes;
    mc_results.p_value_return = p_value;
    mc_results.p_value_sharpe = p_value_sharpe;
    mc_results.is_significant = p_value < 0.05;
    
    % Save results
    save('monte_carlo_results.mat', 'mc_results');
    fprintf('✅ Monte Carlo results saved to: monte_carlo_results.mat\n');
end


function label = get_significance_label(p_value)
    if p_value < 0.01
        label = '*** (Highly Significant)';
    elseif p_value < 0.05
        label = '** (Significant)';
    elseif p_value < 0.10
        label = '* (Marginally Significant)';
    else
        label = '(Not Significant)';
    end
end


function max_dd = calculate_max_drawdown(equity_curve)
    running_max = cummax(equity_curve);
    drawdown = (equity_curve - running_max) ./ running_max * 100;
    max_dd = abs(min(drawdown));
end
