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

type NewUserForm struct {
	Username        string `validate:"alphanum,lowercase,min=3,max=30,required"`
	Password        string `validate:"min=8,required"`
	PasswordConfirm string `validate:"eqcsfield=Password,required"`
}
