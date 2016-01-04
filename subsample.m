function [subX subY] = subsample(X, Y, lab, amount)
%using the unevenly distributed data from X, create a new 
%data distributing by subsampling instances not labeled with lab
%and relable the data with binary lables
%Params:
% n by d matrix X - instance data where n = number of instances
% d vector Y - multiclass labels
% lab - lable that is considered a positive instance
% amount - how much a positive instance of lab should be weighted
%   (the higher the amount, the more negative instances are subsampled)
%NOTE number of rows on X must equal num rows in Y
subX = [];
subY = [];
for i=1:size(X, 1)
    if Y(i) == lab
        subX = [subX(:,:); X(i, :)];
        subY = [subY(:,:); 1];
    elseif rand() < (1/amount)
    %only use 1/amount of the negative instances, this has been shown to be equivalent to weighting positive instances by amound
    %any amount less then 1 means to use all negative instances
        subX = [subX(:,:); X(i, :)];
        subY = [subY(:,:); -1];
    end
end
end

