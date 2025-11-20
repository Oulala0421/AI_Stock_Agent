% run_refined_mc.m
% Driver script to run Monte Carlo validation on the Refined Strategy

function run_refined_mc(symbol, stock_type)
    if nargin < 2
        error('Usage: run_refined_mc(symbol, stock_type)');
    end
    
    data_file = [symbol, '_data.mat'];
    
    fprintf('\n************************************************************\n');
    fprintf('RUNNING MONTE CARLO STRESS TEST FOR %s (%s)\n', symbol, stock_type);
    fprintf('************************************************************\n');
    fflush(stdout);
    
    % 1. Run the refined backtest to get baseline results
    % We need to modify refined_backtest_engine slightly to return the full struct
    % or ensure it returns what monte_carlo_validation needs.
    % refined_backtest_engine returns:
    % results.total_return
    % results.equity_strategy
    % results.equity_buyhold
    % ...
    
    % We need to add 'close' and 'positions' to the results struct in refined_backtest_engine
    % Let's assume we will modify refined_backtest_engine.m first to include these.
    
    try
        results = refined_backtest_engine(data_file, stock_type);
        
        % Add metadata for MC
        results.stock_type = stock_type;
        
        % Load raw data to get 'close' price for MC (if not in results)
        load(data_file, 'close');
        results.close = close;
        
        % Re-derive positions from equity curve if needed, or better, 
        % update refined_backtest_engine to return 'positions'.
        % For now, let's assume we updated refined_backtest_engine to return 'positions'.
        % If not, we can't do Method 1 (Trade Shuffling) accurately without exact trade points.
        % But Method 2 (Permutation) uses 'positions' vector.
        
        % Let's check if 'positions' is in results. 
        % Looking at previous file content of refined_backtest_engine.m:
        % It does NOT return 'positions'. It returns equity_strategy.
        % We MUST update refined_backtest_engine.m to return 'positions'.
        
        % However, since I cannot edit the file in the middle of this script execution,
        % I will rely on the fact that I will update refined_backtest_engine.m BEFORE running this.
        
        % 2. Run Monte Carlo Validation
        monte_carlo_validation(results, 1000);
        
    catch e
        fprintf('Error running MC: %s\n', e.message);
        fprintf('Stack: %s line %d\n', e.stack(1).name, e.stack(1).line);
    end
end
