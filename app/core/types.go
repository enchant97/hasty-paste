package core

import (
	"mime/multipart"
)

type NewPasteFormAttachment struct {
	Slug string `validate:"printascii,required"`
	Type string `validate:"required"`
	Size int64  `validate:"required"`
	Open func() (multipart.File, error)
}

type NewPasteForm struct {
	Slug        string `validate:"printascii,required"`
	Content     string `validate:"required"`
	Visibility  string `validate:"required,oneof=public unlisted private"`
	Attachments []NewPasteFormAttachment
}

type NewUserForm struct {
	Username        string `validate:"alphanum,lowercase,min=3,max=30,required"`
	Password        string `validate:"min=8,required"`
	PasswordConfirm string `validate:"eqcsfield=Password,required"`
}

type LoginUserForm struct {
	Username string `validate:"required"`
	Password string `validate:"required"`
}
