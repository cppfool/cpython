#ifndef Py_FILEUTILS_H
#define Py_FILEUTILS_H

#ifdef __cplusplus
extern "C" {
#endif

PyAPI_FUNC(PyObject *) _Py_device_encoding(int);

PyAPI_FUNC(wchar_t *) Py_DecodeLocale(
    const char *arg,
    size_t *size);

PyAPI_FUNC(char*) Py_EncodeLocale(
    const wchar_t *text,
    size_t *error_pos);

#if defined(HAVE_STAT) && !defined(MS_WINDOWS)
PyAPI_FUNC(int) _Py_wstat(
    const wchar_t* path,
    struct stat *buf);
#endif

#if defined(HAVE_FSTAT) || defined(MS_WINDOWS)

#ifdef MS_WINDOWS
struct _Py_stat_struct {
    unsigned long st_dev;
    __int64 st_ino;
    unsigned short st_mode;
    int st_nlink;
    int st_uid;
    int st_gid;
    unsigned long st_rdev;
    __int64 st_size;
    time_t st_atime;
    int st_atime_nsec;
    time_t st_mtime;
    int st_mtime_nsec;
    time_t st_ctime;
    int st_ctime_nsec;
    unsigned long st_file_attributes;
};
#else
#  define _Py_stat_struct stat
#endif

PyAPI_FUNC(int) _Py_fstat(
    int fd,
    struct _Py_stat_struct *stat);
#endif   /* HAVE_FSTAT || MS_WINDOWS */

#ifdef HAVE_STAT
PyAPI_FUNC(int) _Py_stat(
    PyObject *path,
    struct stat *statbuf);
#endif   /* HAVE_STAT */

#ifndef Py_LIMITED_API
PyAPI_FUNC(int) _Py_open(
    const char *pathname,
    int flags);
#endif

PyAPI_FUNC(FILE *) _Py_wfopen(
    const wchar_t *path,
    const wchar_t *mode);

PyAPI_FUNC(FILE*) _Py_fopen(
    const char *pathname,
    const char *mode);

PyAPI_FUNC(FILE*) _Py_fopen_obj(
    PyObject *path,
    const char *mode);

#ifdef HAVE_READLINK
PyAPI_FUNC(int) _Py_wreadlink(
    const wchar_t *path,
    wchar_t *buf,
    size_t bufsiz);
#endif

#ifdef HAVE_REALPATH
PyAPI_FUNC(wchar_t*) _Py_wrealpath(
    const wchar_t *path,
    wchar_t *resolved_path,
    size_t resolved_path_size);
#endif

PyAPI_FUNC(wchar_t*) _Py_wgetcwd(
    wchar_t *buf,
    size_t size);

#ifndef Py_LIMITED_API
PyAPI_FUNC(int) _Py_get_inheritable(int fd);

PyAPI_FUNC(int) _Py_set_inheritable(int fd, int inheritable,
                                    int *atomic_flag_works);

PyAPI_FUNC(int) _Py_dup(int fd);

#ifndef MS_WINDOWS
PyAPI_FUNC(int) _Py_get_blocking(int fd);

PyAPI_FUNC(int) _Py_set_blocking(int fd, int blocking);
#endif   /* !MS_WINDOWS */

#endif   /* Py_LIMITED_API */

#ifdef __cplusplus
}
#endif

#endif /* !Py_FILEUTILS_H */
