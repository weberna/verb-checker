function [X Y] = trimdata(bX, bY, amount, lab)
%delete amount examples from bX and bY with given label lab 
deleted = 0;
X = bX;
Y= bY;
for i=length(bY):-1:1   %go backwards so we dont mess up the indexes 
    if bY(i) == lab 
        Y(i) = [];
        X(i, :) = [];
        deleted = deleted + 1;
        if deleted >= amount
            break
        end
    end
end
end

