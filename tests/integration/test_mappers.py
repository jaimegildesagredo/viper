# -*- coding: utf-8 -*-

from hamcrest import *
from nose.tools import assert_raises

import pymongo
import gridfs

from viper import mappers
from viper.entities import Package, Release, File


NAME = u'viper'
VERSION = u'0.1dev'
FILE_CONTENT = 'content'


class _TestMapper(object):

    def setup(self):
        self.database = pymongo.Connection()['viper_package_index_test']
        self.cleanup()

    def cleanup(self):
        pass

    def delete_file(self, file_name):
        filesystem = gridfs.GridFS(self.database)
        if filesystem.exists(file_name):
            filesystem.delete(file_name)


class TestPackageMapper(_TestMapper):

    def test_insert_new_package(self):
        new = Package(NAME)

        self.mapper.store(new)

        retrieved = self.mapper.get_by_name(NAME)
        assert_that(retrieved, is_(new))

    def test_insert_new_packages_with_same_twice_raises_already_exists_error(self):
        self.mapper.store(Package(NAME))
        with assert_raises(mappers.AlreadyExistsError):
            self.mapper.store(Package(NAME))

    def test_update_package(self):
        new = Package(NAME)
        self.mapper.store(new)

        new.store_release(Release(VERSION))
        self.mapper.store(new)

        retrieved = self.mapper.get_by_name(NAME)
        assert_that(retrieved, is_(new))

    def test_update_package_updates_last_updated_on(self):
        new = Package(NAME)
        self.mapper.store(new)

        updated = self.mapper.get_by_name(NAME)
        updated.store_release(Release(VERSION))
        self.mapper.store(updated)

        assert_that(updated.last_updated_on, is_(greater_than(new.last_updated_on)))

    def test_raise_error_unless_found(self):
        with assert_raises(mappers.NotFoundError):
            self.mapper.get_by_name(NAME)

    def test_get_all_packages(self):
        new = Package(NAME)
        self.mapper.store(new)

        all_packages = self.mapper.all()

        assert_that(list(all_packages), is_([new]))

    def test_get_all_packages_without_packages(self):
        all_packages = self.mapper.all()

        assert_that(list(all_packages), is_([]))

    def cleanup(self):
        self.database.drop_collection(self.database.packages)

        self.mapper = mappers.PackageMapper(self.database)


class TestFileMapper(_TestMapper):

    def test_insert_new_package(self):
        self.mapper.store(NAME, FILE_CONTENT)

        retrieved = self.mapper.get_by_name(NAME)
        assert_that(retrieved, is_(FILE_CONTENT))

    def test_an_existent_file_cannot_be_upgraded(self):
        self.mapper.store(NAME, FILE_CONTENT)

        with assert_raises(mappers.AlreadyExistsError):
            self.mapper.store(NAME, FILE_CONTENT)

    def test_raise_error_unless_found(self):
        with assert_raises(mappers.NotFoundError):
            self.mapper.get_by_name(NAME)

    def cleanup(self):
        self.delete_file(NAME)

        self.mapper = mappers.FileMapper(self.database)


class TestSONManipulatorCollision(_TestMapper):

    def test_mappers_can_be_used_together(self):
        self.files = mappers.FileMapper(self.database)
        # As PackageMapper sets a custom SONManipulator to database, it should
        # not collision with other mappers
        self.packages = mappers.PackageMapper(self.database)

        self.files.store(NAME, FILE_CONTENT)
        retrieved = self.files.get_by_name(NAME)

        assert_that(retrieved, is_(FILE_CONTENT))

    def cleanup(self):
        self.delete_file(NAME)


class TestSONManipulator(_TestMapper):

    def test_manipulation_sets_releases(self):
        package = self._package()
        self.packages.store(package)

        retrieved = self.packages.get_by_name(NAME)

        assert_that(retrieved.releases(), all_of(has_length(1), has_item(is_(Release))))

    def test_manipulation_sets_files(self):
        package = self._package()
        self.packages.store(package)

        retrieved = self.packages.get_by_name(NAME)

        assert_that(retrieved.release(VERSION).files, has_entry(NAME, is_(File)))

    def _package(self):
        package = Package(NAME)
        release = Release(VERSION)
        package.store_release(release)
        release.add_file(File(NAME, None, None))

        return package

    def cleanup(self):
        self.database.drop_collection(self.database.packages)

        self.packages = mappers.PackageMapper(self.database)


class TestPythonPackageIndex(object):

    def test_exists_a_package(self):
        package = self.pypi.get_by_name(u'tornado')

        assert_that(package.is_from_pypi)
        assert_that(package.name, is_(u'tornado'))
        assert_that(package.releases(), all_of(
            has_length(1),
            has_item(has_property('author', u'Facebook'))
        ))

    def test_raise_error_unless_found(self):
        with assert_raises(mappers.NotFoundError):
            self.pypi.get_by_name(u'I-really-hope-this-package-does-not-exist')

    def setup(self):
        self.pypi = mappers.PythonPackageIndex()
