% simple_backtest.m
% Simplified version for quick testing - no encoding issues

function simple_backtest(symbol)
    if nargin < 1
        symbol = 'SPY';
    end
    
    fprintf('\n=== Simple Backtest: %s ===\n\n', symbol);
    
    % Load data
    data_file = sprintf('%s_data.mat', symbol);
    if ~exist(data_file, 'file')
        fprintf('Error: Data file not found: %s\n', data_file);
        fprintf('Run: python -c "from octave.data_exporter import export_for_backtest; export_for_backtest(''%s'', 5)"\n', symbol);
        return;
    end
    
    load(data_file);
    fprintf('Loaded %d bars\n\n', length(close));
    
    % Simple strategy: RSI oversold + price > MA200
    % Calculate RSI
    rsi_period = 14;
    delta = [0; diff(close)];
    gain = max(delta, 0);
    loss = max(-delta, 0);
    
   % Moving average for gain/loss
    avg_gain = zeros(size(close));
    avg_loss = zeros(size(close));
    for i = rsi_period+1:length(close)
        avg_gain(i) = mean(gain(i-rsi_period+1:i));
        avg_loss(i) = mean(loss(i-rsi_period+1:i));
    end
    
    rs = avg_gain ./ (avg_loss + 0.0001);
    rsi = 100 - (100 ./ (1 + rs));
    
    % MA200
    ma200 = zeros(size(close));
    for i = 200:length(close)
        ma200(i) = mean(close(i-199:i));
    end
    
    % Signals
    signal = (rsi < 30) & (close > ma200);
    
    % Lag to avoid look-ahead
    position = [0; signal(1:end-1)];
    
    % Returns
    returns = [0; diff(log(close))];
    strategy_returns = position .* returns;
    
    % Equity curves
    eq_strategy = cumprod(1 + strategy_returns);
    eq_buyhold = cumprod(1 + returns);
    
    % Metrics
    total_return = (eq_strategy(end) - 1) * 100;
    buyhold_return = (eq_buyhold(end) - 1) * 100;
    
    n_years = length(close) / 252;
    cagr = (eq_strategy(end)^(1/n_years) - 1) * 100;
    
    sharpe = (mean(strategy_returns) / std(strategy_returns)) * sqrt(252);
    
    % Max DD
    running_max = cummax(eq_strategy);
    drawdown = (eq_strategy - running_max) ./ running_max * 100;
    max_dd =abs(min(drawdown));
    
    % Display results
    fprintf('RESULTS:\n');
    fprintf('  Period: %.1f years\n', n_years);
    fprintf('  Strategy Return: %.2f%%\n', total_return);
    fprintf('  Buy & Hold: %.2f%%\n', buyhold_return);
    fprintf('  Alpha: %.2f%%\n', total_return - buyhold_return);
    fprintf('  CAGR: %.2f%%\n', cagr);
    fprintf('  Sharpe: %.3f\n', sharpe);
    fprintf('  Max DD: %.2f%%\n', max_dd);
    fprintf('  Signals: %d\n\n', sum(signal));
    
    if total_return > buyhold_return && sharpe > 0.5
        fprintf('==> WORKS! Strategy shows positive alpha\n\n');
    else
        fprintf('==> Strategy needs improvement\n\n');
    end
end
