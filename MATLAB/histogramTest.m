%Split into RGB Channels
image = thisFrame - Background;
imshow(image);
pause;
Red = image(:,:,1);
Green = image(:,:,2);
Blue = image(:,:,3);
%Get histValues for each channel
[yRed, x] = imhist(Red);
[yGreen, y] = imhist(Green);
[yBlue, z] = imhist(Blue);
%Plot them together in one plot
% plot(x, yRed, 'Red', x, yGreen, 'Green', x, yBlue, 'Blue');

pixels = vidHeight*vidWidth;

r = reshape(Red, pixels,1);
b = reshape(Blue, pixels,1);
g = reshape(Green, pixels,1);

image_reshape = [r g b];
% csvwrite('frame1300.csv',image_reshape)

scatter3(r,g,b,'.')
xlim([0,255]);
ylim([0,255]);
zlim([0,255]);

xlabel('Red');
ylabel('Blue');
zlabel('Green');