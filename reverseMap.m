function rmap = reverseMap(map)
%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
% Reverse the keys and values for
% a containers.Map() object, assuming 
% the values in the map are an object that 
% can be keys
%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%

newKeys = {};
newVals = {};
for k = keys(map)
    newKeys = {newKeys{:} map(k{1})};
    newVals = {newVals{:} k};
end

rmap = containers.Map(newKeys, newVals); 
    
    
    
    
    
