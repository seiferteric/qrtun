# qrtun
IP over qrcode

This implements a tun interface to send biderectional data using qr codes displayed on your monitor and read using your webcam.

Set up two linux PCs with a monitor and webcam facing eachother (a bit finicky to get aligned) and start the program:

On the first computer:
```
sudo python qrtun_async.py 1
```

On the second:
```
sudo python qrtun_async.py 2
```

This will create a qrtun[1|2] interface with 10.0.8.[1|2] on each computer respectively. It will then start reading packets from that interface and show a qrcode in a window for the other to read. The data is base32 encoded due to limations in what characters you can encode in a alphanumeric qr code. Was going to use a tap device but had problems when packets were fragmented with pytun library, but just switched to a tun device and works now!

You can use the up and down arrows to increase/decrease the size of the qr code. You can also press the space bar to toggle camera view mode to show what your camera sees, to help with alignment.

I have only tested on Ubuntu 16.04 and needed these packages:

```
apt-get install qrencode git libzbar-dev python-pygame zbar-tools
pip install python-pytun zbar pillow
pip install git+https://github.com/primetang/qrtools.git
```

Check out these vids!

* [Without seq/ack](https://www.youtube.com/watch?v=_BUlrzEvwEE)
* [First Test](https://www.youtube.com/watch?v=E4qs1FmtDUA)
* [Second](https://www.youtube.com/watch?v=kc9COP5dALU)
* [SSH!](https://www.youtube.com/watch?v=N_Qr5AP_2wU)


[Blog Post](http://seiferteric.com/?p=356)
