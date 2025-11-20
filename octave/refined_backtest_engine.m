% refined_backtest_engine.m
% Improved backtest with RSI percentile and multi-timeframe trend
% Compares old vs new formula

function results = refined_backtest_engine(data_file, stock_type)
    try
        fprintf('\n=== Refined Backtest Engine ===\n');
        fflush(stdout);
        fprintf('Stock Type: %s\n', stock_type);
        fprintf('Formula: RSI Percentile + MA50 Trend + Valuation Penalty\n\n');
        fflush(stdout);
        
        % Load data
        if ~exist(data_file, 'file')
            fprintf('Error: Data file missing: %s\n', data_file);
            return;
        end
        
        load(data_file);
        fprintf('Loaded %d bars\n\n', length(close));
        fflush(stdout);
        
        % === Calculate Indicators ===
        
        % 1. RSI and RSI Percentile
        rsi = calculate_rsi(close, 14);
        rsi_percentile = zeros(size(rsi));
        lookback = 252;  % 1 year
        for i = lookback+1:length(rsi)
            hist = rsi(i-lookback:i-1);
            rsi_percentile(i) = sum(hist < rsi(i)) / lookback;
        end
        
        % 2. Moving Averages
        ma50 = movavg(close, 50, 50, 0);
        ma200 = movavg(close, 200, 200, 0);
        
        % 3. Market Regime (simplified: use MA200)
        market_bullish = close > ma200;
        ma50_above_ma200 = ma50 > ma200;
        
        % 4. Dual Momentum (12-month return)
        returns_12m = zeros(size(close));
        for i = 253:length(close)
            returns_12m(i) = (close(i) - close(i-252)) / close(i-252);
        end
        dual_momentum = returns_12m > 0;
        
        % 5. Bollinger Bands
        bb_period = 20;
        bb_ma = movavg(close, bb_period, bb_period, 0);
        bb_std = zeros(size(close));
        for i = bb_period:length(close)
            bb_std(i) = std(close(i-bb_period+1:i));
        end
        bb_upper = bb_ma + 2 * bb_std;
        bb_lower = bb_ma - 2 * bb_std;
        bb_position = (close - bb_lower) ./ (bb_upper - bb_lower + 0.0001);
        
        % === Generate Signals (New Formula) ===
        
        n = length(close);
        score = zeros(n, 1);
        
        if strcmp(stock_type, 'Core')
            fprintf('Using CORE formula (Long-term hold, buy dips)\n\n');
            
            for i = 253:n  % Start after enough history
                % A. Trend (15%)
                trend = 0;
                if market_bullish(i), trend = trend + 8; end
                if ma50_above_ma200(i), trend = trend + 4; end
                if close(i) > ma200(i), trend = trend + 3; end
                
                % B. Quality (35%) - simplified
                quality = 0;
                if dual_momentum(i), quality = quality + 25; end
                quality = quality + 10;  % Base quality
                
                % C. Value (35%) - Adjusted for Trend Following
                value = 0;
                if rsi_percentile(i) < 0.25, value = value + 20;      % Deep Value
                elseif rsi_percentile(i) < 0.40, value = value + 15;  % Value
                elseif rsi_percentile(i) < 0.60, value = value + 10;  % Neutral/Fair
                elseif rsi_percentile(i) < 0.80, value = value + 5;   % Momentum/Strong
                end
                
                % BB position
                if bb_position(i) < 0.3, value = value + 10;
                elseif bb_position(i) < 0.7, value = value + 5; % Wider range
                end
                
                % D. Cost (15%)
                cost = 10;  % Base
                
                score(i) = trend + quality + value + cost;
            end
            
            % Thresholds - Slightly relaxed to ensure participation
            buy_threshold = 55; 
            sell_threshold = 25; % Hard to sell (Hold Forever)
            
        else  % Satellite
            fprintf('Using SATELLITE formula (Tactical, profit-taking enabled)\n\n');
            
            for i = 253:n
                % A. Trend (20%)
                trend = 0;
                if market_bullish(i), trend = trend + 10; end
                if ma50_above_ma200(i), trend = trend + 5; end
                if dual_momentum(i), trend = trend + 5; end
                
                % B. Quality (30%)
                quality = 0;
                if dual_momentum(i), quality = quality + 25; end
                quality = quality + 5;
                
                % C. Valuation (25%)
                valuation = 10;  % Neutral
                
                % D. Technical (20%) - Momentum & Value
                tech = 0;
                % Reward both Value (Dip) AND Momentum (Trend)
                if rsi_percentile(i) < 0.20, tech = tech + 15;      % Buy the dip
                elseif rsi_percentile(i) < 0.40, tech = tech + 10;
                elseif rsi_percentile(i) > 0.60 && rsi_percentile(i) < 0.90, tech = tech + 10; % Buy the breakout/trend
                elseif rsi_percentile(i) >= 0.40 && rsi_percentile(i) <= 0.60, tech = tech + 5; % Neutral
                end
                
                % Profit-taking penalty - ONLY if extreme extension
                % Don't sell just because RSI is high (let winners run)
                if rsi(i) > 85, tech = tech - 5; % Only extreme overbought
                end
                
                if close(i) < bb_lower(i), tech = tech + 5; end
                
                % E. Sentiment (5%)
                sentiment = 2.5;  % Neutral
                
                score(i) = trend + quality + valuation + tech + sentiment;
            end
            
            buy_threshold = 65;
            sell_threshold = 35; % Lower sell threshold to stay in trend
        end
        
        % Generate signals with hysteresis (State Machine)
        position = zeros(n, 1);
        in_position = false;
        
        for i = 253:n
            if strcmp(stock_type, 'Core')
                % Core: Buy > 60, Sell < 35 (Hardly ever sell)
                if ~in_position && score(i) >= buy_threshold
                    in_position = true;
                elseif in_position && score(i) < sell_threshold
                    in_position = false;
                end
            else
                % Satellite: Buy > 70, Sell < 40 OR Profit Take
                % Profit take: RSI > 75 AND Price > MA200 * 1.3
                is_profit_take = (rsi(i) > 75) && (close(i) > ma200(i) * 1.3);
                
                if ~in_position && score(i) >= buy_threshold
                    in_position = true;
                elseif in_position && (score(i) < sell_threshold || is_profit_take)
                    in_position = false;
                end
            end
            position(i) = in_position;
        end
        
        % Lag to avoid look-ahead bias
        position = [0; position(1:end-1)];
        
        % === Calculate Returns ===
        
        returns = [0; diff(log(close))];
        strategy_returns = position .* returns;
        
        eq_strategy = cumprod(1 + strategy_returns);
        eq_buyhold = cumprod(1 + returns);
        
        % === Performance Metrics ===
        
        total_return = (eq_strategy(end) - 1) * 100;
        buyhold_return = (eq_buyhold(end) - 1) * 100;
        
        n_years = length(close) / 252;
        cagr = (eq_strategy(end)^(1/n_years) - 1) * 100;
        
        sharpe = (mean(strategy_returns) / (std(strategy_returns) + 0.0001)) * sqrt(252);
        
        % Max DD
        running_max = cummax(eq_strategy);
        drawdown = (eq_strategy - running_max) ./ (running_max + 0.0001) * 100;
        max_dd = abs(min(drawdown));
        
        % Win rate
        win_days = sum(strategy_returns(position == 1) > 0);
        total_days_invested = sum(position == 1);
        win_rate = (win_days / (total_days_invested + 1)) * 100;
        
        % === Display Results ===
        
        fprintf('============================================================\n');
        fprintf('REFINED FORMULA RESULTS\n');
        fprintf('============================================================\n\n');
        fflush(stdout);
        
        fprintf('Period: %.1f years (%d bars)\n', n_years, length(close));
        fprintf('Buy Threshold: %d | Sell Threshold: %d\n\n', buy_threshold, sell_threshold);
        
        fprintf('STRATEGY PERFORMANCE:\n');
        fprintf('  Total Return:    %+.2f%%\n', total_return);
        fprintf('  CAGR:            %+.2f%%\n', cagr);
        fprintf('  Sharpe Ratio:    %.3f\n', sharpe);
        fprintf('  Max Drawdown:    %.2f%%\n', max_dd);
        fprintf('  Win Rate:        %.1f%%\n', win_rate);
        fprintf('  Days Invested:   %d / %d (%.1f%%)\n\n', total_days_invested, length(close), (total_days_invested/length(close))*100);
        
        fprintf('BUY & HOLD:\n');
        fprintf('  Total Return:    %+.2f%%\n', buyhold_return);
        fprintf('  Alpha:           %+.2f%%\n\n', total_return - buyhold_return);
        
        % Signal count (raw threshold met)
        signal = score >= buy_threshold;
        fprintf('SIGNALS:\n');
        fprintf('  Buy signals:     %d\n', sum(signal));
        fprintf('  Positions taken: %d periods\n\n', total_days_invested);
        
        if total_return > buyhold_return && sharpe > 0.5
            fprintf('✅ SUCCESS! Refined formula beats buy-and-hold\n\n');
        elseif total_return > buyhold_return
            fprintf('✅ POSITIVE ALPHA but low Sharpe - needs refinement\n\n');
        else
            fprintf('⚠️  NEEDS WORK: Try different thresholds or parameters\n\n');
        end
        
        fprintf('============================================================\n\n');
        fflush(stdout);
        
        % Save summary to file
        summary_file = sprintf('refined_summary_%s.txt', strrep(data_file, '_data.mat', ''));
        fid = fopen(summary_file, 'w');
        fprintf(fid, 'REFINED FORMULA RESULTS\n');
        fprintf(fid, 'Stock Type: %s\n', stock_type);
        fprintf(fid, 'Period: %.1f years\n', n_years);
        fprintf(fid, 'Total Return: %.2f%%\n', total_return);
        fprintf(fid, 'CAGR: %.2f%%\n', cagr);
        fprintf(fid, 'Sharpe: %.3f\n', sharpe);
        fprintf(fid, 'Max Drawdown: %.2f%%\n', max_dd);
        fprintf(fid, 'Win Rate: %.1f%%\n', win_rate);
        fprintf(fid, 'Buy & Hold: %.2f%%\n', buyhold_return);
        fprintf(fid, 'Alpha: %.2f%%\n', total_return - buyhold_return);
        fprintf(fid, 'Signals: %d\n', sum(signal));
        fclose(fid);
        fprintf('Saved results to %s\n', summary_file);
        fflush(stdout);
        
        % Package results
        results = struct();
        results.total_return = total_return;
        results.buyhold_return = buyhold_return;
        results.alpha = total_return - buyhold_return;
        results.cagr = cagr;
        results.sharpe = sharpe;
        results.max_drawdown = max_dd;
        results.win_rate = win_rate;
        results.equity_strategy = eq_strategy;
        results.equity_buyhold = eq_buyhold;
        results.positions = position; % Added for Monte Carlo
        
    catch e
        fprintf('\n❌ ERROR in refined_backtest_engine: %s\n', e.message);
        fprintf('Line: %d\n', e.stack(1).line);
        fflush(stdout);
    end
end


% Helper functions
function rsi = calculate_rsi(prices, period)
    delta = [0; diff(prices)];
    gain = max(delta, 0);
    loss = max(-delta, 0);
    avg_gain = movavg(gain, period, period, 0);
    avg_loss = movavg(loss, period, period, 0);
    rs = avg_gain ./ (avg_loss + 0.0001);
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
