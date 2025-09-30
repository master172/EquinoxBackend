import qrcode
import io
import base64

def generate_qr_code(data):
	qr = qrcode.make(data=data,version=1,box_size=10,border=4)
	buffer = io.BytesIO()
	qr.save(buffer,format="PNG")
	img_str = base64.b64encode(buffer.getvalue()).decode("utf-8")
	return img_str