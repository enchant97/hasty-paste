package core

import "io"

type NewPasteForm struct {
	Slug             string `validate:"printascii,required"`
	AttachmentSlug   string `validate:"printascii,required"`
	AttachmentReader io.ReadSeeker
}
