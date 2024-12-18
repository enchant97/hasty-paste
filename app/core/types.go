package core

import (
	"mime/multipart"
)

type NewPasteFormAttachment struct {
	Slug string `validate:"printascii,required"`
	Open func() (multipart.File, error)
}

type NewPasteForm struct {
	Slug        string `validate:"printascii,required"`
	Content     string `validate:"required"`
	Attachments []NewPasteFormAttachment
}
