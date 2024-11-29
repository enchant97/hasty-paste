package storage

import (
	"errors"
	"io"
	"os"
	"path/filepath"
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
	attachmentUID string,
	r io.Reader,
) error {
	filePath := filepath.Join(sc.rootPath, attachmentUID+".bin")
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
	attachmentUID string,
) (io.ReadCloser, error) {
	filePath := filepath.Join(sc.rootPath, attachmentUID+".bin")
	return os.Open(filePath)
}

func (sc *StorageController) DeletePasteAttachment(
	attachmentUID string,
) error {
	filePath := filepath.Join(sc.rootPath, attachmentUID+".bin")
	return os.Remove(filePath)
}
