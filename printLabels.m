function done = printLabels(file, labels)
%print cell array labels to designated file
fid = fopen(file, 'w');
for i=1:length(labels)
    fprintf(fid, '%s\n', labels{i});
end
fclose(fid);
done=0;
end
    
