package storage

import (
	"errors"
	"io"
	"os"
	"path/filepath"

	"github.com/google/uuid"
)

type StorageController struct {
	rootPath string
}

func (sc StorageController) New(rootPath string) (StorageController, error) {
	if !filepath.IsAbs(rootPath) {
		return StorageController{}, errors.New("rootPath must be a absolute path")
	}
	err := os.MkdirAll(rootPath, 0755)
	return StorageController{
		rootPath: rootPath,
	}, err
}

func (sc *StorageController) WritePasteAttachment(
	attachmentUID uuid.UUID,
	r io.Reader,
) error {
	filePath := filepath.Join(sc.rootPath, attachmentUID.String()+".bin")
	f, err := os.Create(filePath)
	if err != nil {
		return err
	}
	defer f.Close()
	_, err = io.Copy(f, r)
	if err != nil {
		return err
	}
	return nil
}

func (sc *StorageController) ReadPasteAttachment(
	attachmentUID uuid.UUID,
) (io.ReadCloser, error) {
	filePath := filepath.Join(sc.rootPath, attachmentUID.String()+".bin")
	return os.Open(filePath)
}

func (sc *StorageController) DeletePasteAttachment(
	attachmentUID uuid.UUID,
) error {
	filePath := filepath.Join(sc.rootPath, attachmentUID.String()+".bin")
	return os.Remove(filePath)
}
