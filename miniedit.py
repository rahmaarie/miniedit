import streamlit as st
from PIL import Image, ImageEnhance
import io
import pillow_heif
from collections import deque

# Setup halaman
st.set_page_config(page_title="Mini Photoshop", layout="wide")
st.title("🖌️ Mini Photoshop")

# Simpan history gambar & slider untuk Undo & Redo
if "undo_stack" not in st.session_state:
    st.session_state.undo_stack = deque(maxlen=10)
if "redo_stack" not in st.session_state:
    st.session_state.redo_stack = deque(maxlen=10)
if "slider_values" not in st.session_state:
    st.session_state.slider_values = {"brightness": 1.0, "contrast": 1.0, "width": None, "height": None, "rotate": 0, "flip_h": False, "flip_v": False}

# Upload file gambar
uploaded_file = st.file_uploader("Pilih gambar...", type=["jpg", "png", "jpeg", "heic"])

if uploaded_file:
    file_extension = uploaded_file.name.split(".")[-1].lower()
def heic_to_pil(image_file):
    heif_file = pyheif.read(image_file.read())
    image = Image.frombytes(
        heif_file.mode, 
        heif_file.size, 
        heif_file.data)
    return image
    
if file_extension == "heic":
    image = heic_to_pil(uploaded_file)
else:
    image = Image.open(uploaded_file)

    # Tampilkan gambar
    st.image(image, caption="Gambar yang Diupload", use_column_width=True)
    # Reset state jika gambar baru diunggah
    if "current_image" not in st.session_state or st.session_state.current_image is None:
        st.session_state.current_image = image.copy()
        st.session_state.undo_stack.clear()
        st.session_state.redo_stack.clear()
        st.session_state.undo_stack.append((image.copy(), dict(st.session_state.slider_values)))
        st.session_state.slider_values["width"] = image.width
        st.session_state.slider_values["height"] = image.height

    # Sidebar untuk toolbar
    st.sidebar.title("🎛️ Toolbar")

    # Gunakan key agar slider menyimpan nilai di session_state
    brightness = st.sidebar.slider("Brightness", 0.1, 2.0, st.session_state.slider_values["brightness"], key="brightness")
    contrast = st.sidebar.slider("Contrast", 0.1, 2.0, st.session_state.slider_values["contrast"], key="contrast")
    
    # Resize
    resize_width = st.sidebar.number_input("Resize Width", min_value=10, value=st.session_state.slider_values["width"], key="width")
    resize_height = st.sidebar.number_input("Resize Height", min_value=10, value=st.session_state.slider_values["height"], key="height")
    
    # Rotate & Flip
    rotate_angle = st.sidebar.slider("Rotate", -180, 180, st.session_state.slider_values["rotate"], key="rotate")
    flip_horizontal = st.sidebar.checkbox("Flip Horizontal", value=st.session_state.slider_values["flip_h"], key="flip_h")
    flip_vertical = st.sidebar.checkbox("Flip Vertical", value=st.session_state.slider_values["flip_v"], key="flip_v")

    # Jika ada perubahan, simpan ke history
    if (
        brightness != st.session_state.slider_values["brightness"] or
        contrast != st.session_state.slider_values["contrast"] or
        resize_width != st.session_state.slider_values["width"] or
        resize_height != st.session_state.slider_values["height"] or
        rotate_angle != st.session_state.slider_values["rotate"] or
        flip_horizontal != st.session_state.slider_values["flip_h"] or
        flip_vertical != st.session_state.slider_values["flip_v"]
    ):
        # Simpan state sebelum perubahan untuk Undo
        st.session_state.undo_stack.append((st.session_state.current_image.copy(), dict(st.session_state.slider_values)))
        st.session_state.redo_stack.clear()

        # Perbarui nilai slider di session_state
        st.session_state.slider_values.update({
            "brightness": brightness, "contrast": contrast,
            "width": resize_width, "height": resize_height,
            "rotate": rotate_angle, "flip_h": flip_horizontal, "flip_v": flip_vertical
        })

        # Copy gambar sebelum diedit
        edited_image = st.session_state.current_image.copy()

        # Apply perubahan
        enhancer = ImageEnhance.Brightness(edited_image)
        edited_image = enhancer.enhance(brightness)
        enhancer = ImageEnhance.Contrast(edited_image)
        edited_image = enhancer.enhance(contrast)

        edited_image = edited_image.resize((resize_width, resize_height))
        edited_image = edited_image.rotate(rotate_angle)

        if flip_horizontal:
            edited_image = edited_image.transpose(Image.FLIP_LEFT_RIGHT)
        if flip_vertical:
            edited_image = edited_image.transpose(Image.FLIP_TOP_BOTTOM)

        # Simpan hasil editan sebagai gambar terbaru
        st.session_state.current_image = edited_image.copy()

    # Tampilkan hasil editan
    st.image(st.session_state.current_image, caption="Gambar yang Diedit", use_column_width=True)

    # Tombol Undo dan Redo
    col1, col2 = st.columns(2)

    with col1:
        if st.button("↩️ Undo") and len(st.session_state.undo_stack) > 1:
            st.session_state.redo_stack.append((st.session_state.current_image.copy(), dict(st.session_state.slider_values)))
            st.session_state.current_image, st.session_state.slider_values = st.session_state.undo_stack.pop()
            st.rerun()  # **Ganti st.experimental_rerun() dengan st.rerun()**

    with col2:
        if st.button("↪️ Redo") and st.session_state.redo_stack:
            st.session_state.undo_stack.append((st.session_state.current_image.copy(), dict(st.session_state.slider_values)))
            st.session_state.current_image, st.session_state.slider_values = st.session_state.redo_stack.pop()
            st.rerun()  # **Ganti st.experimental_rerun() dengan st.rerun()**

    # Tombol download
    img_bytes = io.BytesIO()
    st.session_state.current_image.save(img_bytes, format="PNG")
    st.download_button(label="💾 Download Gambar", data=img_bytes.getvalue(), file_name="edited_image.png", mime="image/png")
