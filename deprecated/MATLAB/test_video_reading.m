clc;
close all;
imtool close all;
clear;

movieFullFileName = 'test2.mp4';

if ~exist(movieFullFileName, 'file')
	strErrorMessage = sprintf('File not found:\n%s\nYou can choose a new one, or cancel', movieFullFileName);
	response = questdlg(strErrorMessage, 'File not found', 'OK - choose a new movie.', 'Cancel', 'OK - choose a new movie.');
	if strcmpi(response, 'OK - choose a new movie.')
		[baseFileName, folderName, FilterIndex] = uigetfile('*.avi');
		if ~isequal(baseFileName, 0)
			movieFullFileName = fullfile(folderName, baseFileName);
		else
			return;
		end
	else
		return;
	end
end

try
	videoObject = VideoReader(movieFullFileName)
	% Determine how many frames there are.
	numberOfFrames = videoObject.NumberOfFrames;
	vidHeight = videoObject.Height;
	vidWidth = videoObject.Width;
	
	numberOfFramesWritten = 0;

    diffs = zeros(numberOfFrames, 2);
    diffs(:,2) = linspace(1,7803,7803);
    
	for frame = 1 : numberOfFrames
		% Extract the frame from the movie structure.
		thisFrame = read(videoObject, frame);
		
		numberOfFramesWritten = numberOfFramesWritten + 1;
		
		% Now let's do the differencing
		alpha = 0.5;
		if frame == 1
			BackGround = thisFrame;
        else
			% Change background slightly at each frame
			% 			Background(t+1)=(1-alpha)*I+alpha*Background
		end

		differenceImage = thisFrame - BackGround;
        
        sumDiff = sum(sum(sum(differenceImage)));
  
        diffs(frame,1) = sumDiff;
        
        progressIndication = sprintf('Processed frame %4d of %d, with %d diff.', frame, numberOfFrames, sumDiff);
		disp(progressIndication);
        
        BackGround = thisFrame;
        
	end

    finishedMessage = sprintf('Done!  It processed %d frames of\n"%s"', numberOfFramesWritten, movieFullFileName);
	disp(finishedMessage); % Write to command window.
	
catch ME
	% Some error happened if you get here.
	strErrorMessage = sprintf('Error extracting movie frames from:\n\n%s\n\nError: %s\n\n)', movieFullFileName, ME.message);
	uiwait(msgbox(strErrorMessage));
end
