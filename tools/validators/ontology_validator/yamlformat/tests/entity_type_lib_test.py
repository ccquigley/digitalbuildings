# Copyright 2020 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the License);
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an AS IS BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
"""Tests for bizapps.rews.carson.ontology.validation.entity_type_lib."""

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
import os
from absl.testing import absltest
from yamlformat.validator import entity_type_lib
from yamlformat.validator import field_lib
from yamlformat.validator import findings_lib
from yamlformat.validator import test_helpers_lib

_GOOD_PATH_FORMAT = '{0}/entity_types/anyfolder'
_GOOD_PATH = _GOOD_PATH_FORMAT.format('mynamespace')
_GOOD_PATH_2 = _GOOD_PATH_FORMAT.format('mynamespace2')

_FS = test_helpers_lib.Fields
_F = test_helpers_lib.Field

_GUID_1 = '4d68ac84-786f-425c-9a65-097b1fb04c91'
_GUID_2 = '3d68ac84-786f-425c-9a65-097b1fb04c91'


# pylint: disable=protected-access
class EntityTypeLibTest(absltest.TestCase):

  def testEntityTypeUniverseGetFindings(self):
    filepath = _GOOD_PATH + '/file.yaml'
    context = findings_lib.FileContext(filepath)
    folder = entity_type_lib.EntityTypeFolder(_GOOD_PATH)
    folder.AddFinding(findings_lib.InconsistentFileLocationError('', context))
    namespace = folder.local_namespace
    namespace.AddFinding(findings_lib.InvalidTypenameError('two', context))
    # This will generate a MissingDescriptionWarning on itself
    entity_type = entity_type_lib.EntityType(
        typename='one', filepath=filepath, guid=_GUID_1
    )
    namespace.InsertType(entity_type)

    types_universe = entity_type_lib.EntityTypeUniverse([folder])

    findings = types_universe.GetFindings()
    self.assertLen(findings, 3)
    self.assertTrue(
        types_universe.HasFindingTypes([
            findings_lib.InconsistentFileLocationError,
            findings_lib.InvalidTypenameError,
            findings_lib.MissingEntityTypeDescriptionWarning,
        ])
    )
    self.assertFalse(types_universe.IsValid())

  def testEntityTypeUniverseFindsDupGuids(self):
    filepath = _GOOD_PATH + '/file.yaml'
    folder = entity_type_lib.EntityTypeFolder(_GOOD_PATH)
    namespace = folder.local_namespace

    entity_type1 = entity_type_lib.EntityType(
        typename='one', filepath=filepath, description='hi', guid=_GUID_1
    )
    namespace.InsertType(entity_type1)
    entity_type1a = entity_type_lib.EntityType(
        typename='oneA', filepath=filepath, description='hi', guid=_GUID_1
    )
    namespace.InsertType(entity_type1a)
    entity_type2 = entity_type_lib.EntityType(
        typename='two', filepath=filepath, description='hi', guid=_GUID_2
    )
    namespace.InsertType(entity_type2)

    types_universe = entity_type_lib.EntityTypeUniverse([folder])

    findings = types_universe.GetFindings()
    self.assertLen(findings, 2)
    self.assertTrue(
        types_universe.HasFindingTypes([findings_lib.DuplicateGuidsError])
    )
    self.assertTrue(
        entity_type1.HasFindingTypes([findings_lib.DuplicateGuidsError])
    )
    self.assertTrue(
        entity_type1a.HasFindingTypes([findings_lib.DuplicateGuidsError])
    )
    self.assertFalse(entity_type2.GetFindings())

  def testEntityTypeUniverseFindsInvalidGuids(self):
    filepath = _GOOD_PATH + '/file.yaml'
    folder = entity_type_lib.EntityTypeFolder(_GOOD_PATH)
    namespace = folder.local_namespace

    entity_type1 = entity_type_lib.EntityType(
        typename='one', filepath=filepath, description='hi', guid='1'
    )
    namespace.InsertType(entity_type1)
    entity_type2 = entity_type_lib.EntityType(
        typename='two', filepath=filepath, description='hi', guid=_GUID_1
    )
    namespace.InsertType(entity_type2)

    types_universe = entity_type_lib.EntityTypeUniverse([folder])

    findings = types_universe.GetFindings()
    self.assertLen(findings, 1)
    self.assertTrue(
        types_universe.HasFindingTypes([findings_lib.InvalidTypeGuidError])
    )
    self.assertTrue(
        entity_type1.HasFindingTypes([findings_lib.InvalidTypeGuidError])
    )
    self.assertFalse(entity_type2.GetFindings())

  def testEntityTypeUniverseFindsMissingGuids(self):
    filepath = _GOOD_PATH + '/file.yaml'
    folder = entity_type_lib.EntityTypeFolder(_GOOD_PATH)
    namespace = folder.local_namespace

    entity_type1 = entity_type_lib.EntityType(
        typename='one', filepath=filepath, description='hi', guid=_GUID_1
    )
    namespace.InsertType(entity_type1)
    entity_type2 = entity_type_lib.EntityType(
        typename='two', filepath=filepath, description='hi'
    )
    namespace.InsertType(entity_type2)

    types_universe = entity_type_lib.EntityTypeUniverse([folder])

    findings = types_universe.GetFindings()
    self.assertLen(findings, 1)
    self.assertTrue(
        types_universe.HasFindingTypes([findings_lib.MissingTypeGuidError])
    )
    self.assertTrue(
        entity_type2.HasFindingTypes([findings_lib.MissingTypeGuidError])
    )
    self.assertFalse(entity_type1.GetFindings())

  def testEntityTypeUniverseHandlesNamespaceMovesWithGuids(self):
    filepath = _GOOD_PATH + '/file.yaml'
    folder = entity_type_lib.EntityTypeFolder(_GOOD_PATH)
    namespace = folder.local_namespace

    filepath2 = _GOOD_PATH_2 + '/file.yaml'
    folder2 = entity_type_lib.EntityTypeFolder(_GOOD_PATH_2)
    namespace2 = folder2.local_namespace

    entity_type1 = entity_type_lib.EntityType(
        typename='one', filepath=filepath, description='hi', guid=_GUID_1
    )
    namespace.InsertType(entity_type1)
    entity_type1a = entity_type_lib.EntityType(
        typename='oneA', filepath=filepath2, description='hi', guid=_GUID_1
    )
    namespace2.InsertType(entity_type1a)

    types_universe = entity_type_lib.EntityTypeUniverse([folder, folder2])

    findings = types_universe.GetFindings()
    self.assertLen(findings, 2)
    self.assertTrue(
        types_universe.HasFindingTypes([findings_lib.DuplicateGuidsError])
    )
    self.assertTrue(
        entity_type1.HasFindingTypes([findings_lib.DuplicateGuidsError])
    )
    self.assertTrue(
        entity_type1a.HasFindingTypes([findings_lib.DuplicateGuidsError])
    )

  # -------------------------------------------------------------------------- #
  # Tests for EntityTypeFolder class
  # -------------------------------------------------------------------------- #

  def testCreateTypeFolderSuccess(self):
    folderpath = 'NS/entity_types'
    type_folder = entity_type_lib.EntityTypeFolder(folderpath)
    self.assertFalse(type_folder.GetFindings())

  def testCreateTypeFolderSuccessWithSubfolder(self):
    folderpath = 'NS/entity_types/subfolder'
    type_folder = entity_type_lib.EntityTypeFolder(folderpath)
    self.assertFalse(type_folder.GetFindings())

  def testCreateTypeFolderFailure(self):
    bad_folderpath = 'NS/bad'
    with self.assertRaises(RuntimeError):
      entity_type_lib.EntityTypeFolder(bad_folderpath)

  def testAddFromConfigExtraKeys(self):
    folderpath = 'ANIMAL/entity_types'
    # don't supply a fields_universe
    type_folder = entity_type_lib.EntityTypeFolder(folderpath)
    self.assertFalse(type_folder.GetFindings())

    good_filepath = os.path.join(folderpath, 'mammal.yaml')
    # Build test proto
    yaml_doc = {
        'cat': {
            'guid': _GUID_1,
            'description': 'feline animal',
            'uses': ['meow', 'claws'],
            'implements': ['fuzzy'],
            'notakey': 'stuff',
        }
    }

    type_folder.AddFromConfig([yaml_doc], good_filepath)
    self.assertTrue(
        type_folder.HasFindingTypes([findings_lib.UnrecognizedKeyError])
    )

  def testAddFromConfig(self):
    folderpath = 'ANIMAL/entity_types'
    # don't supply a fields_universe
    type_folder = entity_type_lib.EntityTypeFolder(folderpath)
    self.assertFalse(type_folder.GetFindings())

    good_filepath = os.path.join(folderpath, 'mammal.yaml')
    # Build test proto
    yaml_doc = {
        'cat': {
            'guid': _GUID_1,
            'description': 'feline animal',
            'uses': ['meow', 'claws'],
            'opt_uses': ['cuddle'],
            'implements': ['fuzzy'],
        }
    }

    type_folder.AddFromConfig([yaml_doc], good_filepath)
    self.assertFalse(type_folder.GetFindings())
    self.assertFalse(type_folder.local_namespace.GetFindings())
    self.assertLen(type_folder.local_namespace.valid_types_map, 1)
    new_type = type_folder.local_namespace.valid_types_map['cat']
    self.assertCountEqual(
        ['/meow', '/claws', '/cuddle'], new_type.local_field_names
    )
    self.assertCountEqual(['fuzzy'], new_type.unqualified_parent_names)
    self.assertEqual('feline animal', new_type.description)
    self.assertEqual(good_filepath, new_type.file_context.filepath)

  def testAddFromConfigBadLocation(self):
    folderpath = 'ANIMAL/entity_types'
    type_folder = entity_type_lib.EntityTypeFolder(folderpath)
    self.assertFalse(type_folder.GetFindings())

    bad_typepath = os.path.join('something', 'INSECT/entity_types/ant')
    type_folder.AddFromConfig([], bad_typepath)
    self.assertTrue(
        type_folder.HasFindingTypes(
            [findings_lib.InconsistentFileLocationError]
        )
    )

  def testAddGoodType(self):
    fields_universe = field_lib.FieldUniverse([])
    fields_universe._namespace_map = {
        '': [field_lib.Field('animal')],
        'ANIMAL': [field_lib.Field('meow'), field_lib.Field('claws')],
    }
    folderpath = 'ANIMAL/entity_types'
    type_folder = entity_type_lib.EntityTypeFolder(folderpath, fields_universe)
    self.assertFalse(type_folder.GetFindings())

    rel_typepath = os.path.join(folderpath, 'mammal')
    entity_type = entity_type_lib.EntityType(
        filepath=rel_typepath,
        typename='cat',
        description='feline animal',
        local_field_tuples=_FS(['ANIMAL/meow', 'ANIMAL/claws', '/animal']),
        guid=_GUID_1,
    )
    type_folder._AddType(entity_type)

    self.assertFalse(type_folder.local_namespace.GetFindings())
    self.assertLen(type_folder.local_namespace.valid_types_map, 1)
    self.assertIn(
        entity_type.typename, type_folder.local_namespace.valid_types_map
    )
    self.assertEqual(
        type_folder.local_namespace.valid_types_map.get(entity_type.typename),
        entity_type,
    )

  def testAddGoodTypeWithIncrementedFields(self):
    fields_universe = field_lib.FieldUniverse([])
    fields_universe._namespace_map = {
        '': [field_lib.Field('animal')],
        'ANIMAL': [field_lib.Field('meow'), field_lib.Field('claws')],
    }
    folderpath = 'ANIMAL/entity_types'
    type_folder = entity_type_lib.EntityTypeFolder(folderpath, fields_universe)

    self.assertFalse(type_folder.GetFindings())

    rel_typepath = os.path.join(folderpath, 'mammal')
    entity_type = entity_type_lib.EntityType(
        filepath=rel_typepath,
        typename='cat',
        description='feline animal',
        local_field_tuples=_FS(
            ['ANIMAL/meow_1', 'ANIMAL/claws_1_1', '/animal_2_1']
        ),
        guid=_GUID_1,
    )
    type_folder._AddType(entity_type)

    self.assertFalse(type_folder.local_namespace.GetFindings())
    self.assertLen(type_folder.local_namespace.valid_types_map, 1)
    self.assertIn(
        entity_type.typename, type_folder.local_namespace.valid_types_map
    )
    self.assertEqual(
        type_folder.local_namespace.valid_types_map.get(entity_type.typename),
        entity_type,
    )

  def testAddTypeWithNamespacedField(self):
    fields_universe = field_lib.FieldUniverse([])
    fields_universe._namespace_map = {
        '': [field_lib.Field('animal')],
        'ANIMAL': [field_lib.Field('meow')],
        'ATTACK': [field_lib.Field('claws')],
    }
    folderpath = 'ANIMAL/entity_types'
    type_folder = entity_type_lib.EntityTypeFolder(folderpath, fields_universe)
    self.assertFalse(type_folder.GetFindings())

    rel_typepath = os.path.join(folderpath, 'mammal')

    # field 'claws' is undefined.
    entity_type = entity_type_lib.EntityType(
        filepath=rel_typepath,
        typename='cat',
        description='feline animal',
        local_field_tuples=_FS(['ANIMAL/meow', 'ATTACK/claws', '/animal']),
        guid=_GUID_1,
    )
    type_folder._AddType(entity_type)

    self.assertFalse(type_folder.local_namespace.GetFindings())
    self.assertLen(type_folder.local_namespace.valid_types_map, 1)
    self.assertIn(
        entity_type.typename, type_folder.local_namespace.valid_types_map
    )
    self.assertEqual(
        type_folder.local_namespace.valid_types_map.get(entity_type.typename),
        entity_type,
    )

  def testAddTypeUndefinedFields(self):
    fields_universe = field_lib.FieldUniverse([])
    fields_universe._namespace_map = {
        '': [field_lib.Field('animal')],
        'ANIMAL': [field_lib.Field('meow')],
    }
    folderpath = 'ANIMAL/entity_types'
    type_folder = entity_type_lib.EntityTypeFolder(folderpath, fields_universe)
    self.assertFalse(type_folder.GetFindings())

    rel_typepath = os.path.join(folderpath, 'mammal')

    # field 'claws' is undefined.
    entity_type = entity_type_lib.EntityType(
        filepath=rel_typepath,
        typename='cat',
        description='feline animal',
        local_field_tuples=_FS(['ANIMAL/meow', 'ANIMAL/claws', '/animal']),
        guid=_GUID_1,
    )
    type_folder._AddType(entity_type)
    self.assertTrue(
        type_folder.local_namespace.HasFindingTypes(
            [findings_lib.UndefinedFieldError]
        )
    )
    self.assertFalse(type_folder.local_namespace.valid_types_map)

  def testAddMultipleTypes(self):
    fields_universe = field_lib.FieldUniverse([])
    fields_universe._namespace_map = {
        '': [field_lib.Field('animal')],
        'ANIMAL': [field_lib.Field('meow')],
    }
    folderpath = 'ANIMAL/entity_types'
    type_folder = entity_type_lib.EntityTypeFolder(folderpath, fields_universe)
    self.assertFalse(type_folder.GetFindings())

    rel_typepath = os.path.join(folderpath, 'mammal')
    # bad entity type, field 'claws' is undefined.
    bad_type = entity_type_lib.EntityType(
        filepath=rel_typepath,
        typename='cat',
        description='feline animal',
        local_field_tuples=_FS(['ANIMAL/meow', 'ANIMAL/claws', '/animal']),
        guid=_GUID_1,
    )
    # good entity type
    good_type = entity_type_lib.EntityType(
        filepath=rel_typepath,
        typename='kitty',
        description='feline animal',
        local_field_tuples=_FS(['ANIMAL/meow', '/animal']),
        guid=_GUID_2,
    )
    type_folder._AddType(good_type)
    type_folder._AddType(bad_type)

    self.assertTrue(
        type_folder.local_namespace.HasFindingTypes(
            [findings_lib.UndefinedFieldError]
        )
    )
    self.assertLen(type_folder.local_namespace.valid_types_map, 1)
    self.assertIn(
        good_type.typename, type_folder.local_namespace.valid_types_map
    )
    self.assertEqual(
        type_folder.local_namespace.valid_types_map.get(good_type.typename),
        good_type,
    )

  def testAddDuplicateTypes(self):
    fields_universe = field_lib.FieldUniverse([])
    fields_universe._namespace_map = {
        '': [field_lib.Field('animal')],
        'ANIMAL': [field_lib.Field('meow')],
    }
    folderpath = 'ANIMAL/entity_types'
    type_folder = entity_type_lib.EntityTypeFolder(folderpath, fields_universe)
    self.assertFalse(type_folder.GetFindings())

    rel_typepath = os.path.join(folderpath, 'mammal')
    # entity type
    entity_type = entity_type_lib.EntityType(
        filepath=rel_typepath,
        typename='kitty',
        description='feline animal',
        local_field_tuples=_FS(['ANIMAL/meow', '/animal']),
        guid=_GUID_1,
    )
    # duplicate type
    dup_type = entity_type_lib.EntityType(
        filepath=rel_typepath,
        typename='kitty',
        description='feline animal',
        local_field_tuples=_FS(['ANIMAL/meow', '/animal']),
        guid=_GUID_2,
    )

    type_folder._AddType(entity_type)
    type_folder._AddType(dup_type)

    self.assertTrue(
        type_folder.local_namespace.HasFindingTypes(
            [findings_lib.DuplicateEntityTypeDefinitionError]
        )
    )
    self.assertLen(type_folder.local_namespace.valid_types_map, 1)
    self.assertIn(
        entity_type.typename, type_folder.local_namespace.valid_types_map
    )
    self.assertEqual(
        type_folder.local_namespace.valid_types_map.get(entity_type.typename),
        entity_type,
    )

  # -------------------------------------------------------------------------- #
  # Tests for EntityType class
  # -------------------------------------------------------------------------- #

  def testGoodEntityType(self):
    entity_type = entity_type_lib.EntityType(
        filepath='path/to/ANIMAL/mammal',
        typename='dog',
        description='canine animal',
        local_field_tuples=_FS(['/woof', '/wag']),
        parents=['wolf', 'ANIMAL', 'dingo'],
        guid=_GUID_1,
    )

    self.assertFalse(entity_type.GetFindings())
    self.assertTrue(entity_type.IsValid())

  def testDuplicateFields(self):
    # this should ignore whether or not a field is optional
    entity_type = entity_type_lib.EntityType(
        filepath='path/to/ANIMAL/mammal',
        typename='cat',
        description='feline animal',
        local_field_tuples=[
            _F('/meow', True),
            _F('/claws', False),
            _F('/meow', False),
        ],
        guid=_GUID_1,
    )

    errors = entity_type.GetFindings()
    self.assertLen(errors, 1)
    self.assertTrue(
        entity_type.HasFindingTypes([findings_lib.DuplicateFieldError])
    )
    self.assertFalse(entity_type.IsValid())

  def testDuplicateFieldsWithDifferentCaps(self):
    entity_type = entity_type_lib.EntityType(
        filepath='path/to/ANIMAL/mammal',
        typename='cat',
        description='feline animal',
        local_field_tuples=_FS(['/mEow', '/claws', '/meow']),
        guid=_GUID_1,
    )

    errors = entity_type.GetFindings()
    self.assertLen(errors, 1)
    self.assertTrue(
        entity_type.HasFindingTypes([findings_lib.DuplicateFieldError])
    )
    self.assertFalse(entity_type.IsValid())

  def testBadFieldFormat(self):
    entity_type = entity_type_lib.EntityType(
        filepath='path/to/ANIMAL/mammal',
        typename='cat',
        description='feline animal',
        local_field_tuples=_FS(['/meow', 'NS/wrong/claws']),
        guid=_GUID_1,
    )

    errors = entity_type.GetFindings()
    self.assertLen(errors, 1)
    self.assertTrue(
        entity_type.HasFindingTypes([findings_lib.UnrecognizedFieldFormatError])
    )
    self.assertFalse(entity_type.IsValid())

  def testDuplicateParents(self):
    entity_type = entity_type_lib.EntityType(
        filepath='path/to/ANIMAL/mammal',
        typename='dog',
        description='canine animal',
        parents=['wolf', 'wolf'],
        guid=_GUID_1,
    )

    errors = entity_type.GetFindings()
    self.assertLen(errors, 1)
    self.assertTrue(
        entity_type.HasFindingTypes([findings_lib.DuplicateParentError])
    )
    self.assertFalse(entity_type.IsValid())

  def testMissingTypename(self):
    entity_type = entity_type_lib.EntityType(
        filepath='path/to/ANIMAL/mammal',
        description='canine animal',
        local_field_tuples=_FS(['/woof', '/wag']),
        guid=_GUID_1,
    )

    errors = entity_type.GetFindings()
    self.assertLen(errors, 1)
    self.assertTrue(
        entity_type.HasFindingTypes([findings_lib.MissingTypenameError])
    )
    self.assertFalse(entity_type.IsValid())

  def testIllegalTypenameType(self):
    entity_type = entity_type_lib.EntityType(
        filepath='path/to/ANIMAL/mammal',
        typename=True,
        description='false',
        guid=_GUID_1,
    )

    errors = entity_type.GetFindings()
    self.assertLen(errors, 1)
    self.assertTrue(
        entity_type.HasFindingTypes([findings_lib.IllegalKeyTypeError])
    )
    self.assertFalse(entity_type.IsValid())

  def testMissingDescription(self):
    entity_type = entity_type_lib.EntityType(
        filepath='path/to/ANIMAL/mammal', typename='dog', guid=_GUID_1
    )

    errors = entity_type.GetFindings()
    self.assertLen(errors, 1)
    self.assertTrue(
        entity_type.HasFindingTypes(
            [findings_lib.MissingEntityTypeDescriptionWarning]
        )
    )
    self.assertTrue(entity_type.IsValid())

  def testIllegalAbstractPassthroughType(self):
    entity_type = entity_type_lib.EntityType(
        filepath='path/to/ANIMAL/mammal',
        typename='dog',
        description='canine animal',
        is_abstract=True,
        allow_undefined_fields=True,
        guid=_GUID_1,
    )

    errors = entity_type.GetFindings()
    self.assertLen(errors, 1)
    self.assertTrue(
        entity_type.HasFindingTypes([findings_lib.AbstractPassthroughTypeError])
    )
    self.assertFalse(entity_type.IsValid())

  def testInheritedFieldsSet(self):
    entity_type = entity_type_lib.EntityType(
        filepath='path/to/ANIMAL/mammal',
        typename='dog',
        description='canine animal',
        local_field_tuples=_FS(['/woof', '/wag']),
        inherited_fields_expanded=True,
        guid=_GUID_1,
    )

    errors = entity_type.GetFindings()
    self.assertLen(errors, 1)
    self.assertTrue(
        entity_type.HasFindingTypes([findings_lib.InheritedFieldsSetError])
    )
    self.assertFalse(entity_type.IsValid())

  def testMultipleErrors(self):
    entity_type = entity_type_lib.EntityType(
        filepath='path/to/ANIMAL/mammal',
        description='canine animal',
        local_field_tuples=_FS(['/woof', '/wag', '/woof']),
        parents=['wolf', 'wolf'],
        guid=_GUID_1,
    )

    errors = entity_type.GetFindings()
    self.assertLen(errors, 3)
    self.assertTrue(
        entity_type.HasFindingTypes([findings_lib.MissingTypenameError])
    )
    self.assertTrue(
        entity_type.HasFindingTypes([findings_lib.DuplicateFieldError])
    )
    self.assertTrue(
        entity_type.HasFindingTypes([findings_lib.DuplicateParentError])
    )
    self.assertFalse(entity_type.IsValid())

  def testParseFieldWithIncrement(self):
    field_name, increment = entity_type_lib.SeparateFieldIncrement(
        'zone_occupancy_status_1'
    )

    self.assertEqual(field_name, 'zone_occupancy_status')
    self.assertEqual(increment, '_1')

  def testParseFieldWithoutIncrement(self):
    field_name, increment = entity_type_lib.SeparateFieldIncrement(
        'zone_occupancy_status'
    )

    self.assertEqual(field_name, 'zone_occupancy_status')
    self.assertEqual(increment, '')

  def testHasField(self):
    entity_type = entity_type_lib.EntityType(
        filepath='path/to/ANIMAL/mammal',
        description='canine animal',
        local_field_tuples=_FS(['HAPPY/wag']),
        inherited_fields_expanded=True,
        guid=_GUID_1,
    )
    entity_type.inherited_field_names['/woof'] = _F('/woof')

    self.assertTrue(entity_type.HasField('HAPPY/wag'))
    self.assertTrue(entity_type.HasField('/woof'))
    self.assertFalse(entity_type.HasField('SAD/wag'))

  def testHasFieldAsWritten(self):
    entity_type = entity_type_lib.EntityType(
        filepath='path/to/ANIMAL/mammal',
        description='canine animal',
        local_field_tuples=_FS(['HAPPY/wag', '/woof', 'ANIMALS/fuzzy']),
        inherited_fields_expanded=True,
        namespace=entity_type_lib.TypeNamespace('ANIMALS'),
        guid=_GUID_1,
    )

    self.assertTrue(entity_type.HasFieldAsWritten('fuzzy'))
    self.assertTrue(entity_type.HasFieldAsWritten('ANIMALS/fuzzy'))
    self.assertTrue(entity_type.HasFieldAsWritten('HAPPY/wag'))
    self.assertTrue(entity_type.HasFieldAsWritten('woof'))
    self.assertTrue(entity_type.HasFieldAsWritten('/woof'))

    self.assertFalse(entity_type.HasFieldAsWritten('/wag'))
    self.assertFalse(entity_type.HasFieldAsWritten('wag'))

  def testGetFieldFromConfigText(self):
    entity_type = entity_type_lib.EntityType(
        filepath='path/to/ANIMAL/mammal',
        description='canine animal',
        local_field_tuples=_FS(['HAPPY/wag', '/woof', 'ANIMALS/fuzzy']),
        inherited_fields_expanded=True,
        namespace=entity_type_lib.TypeNamespace('ANIMALS'),
        guid=_GUID_1,
    )
    self.assertEqual(
        'fuzzy', entity_type.GetFieldFromConfigText('fuzzy').field.field
    )
    self.assertEqual(
        'fuzzy', entity_type.GetFieldFromConfigText('ANIMALS/fuzzy').field.field
    )
    self.assertEqual(
        'wag', entity_type.GetFieldFromConfigText('HAPPY/wag').field.field
    )
    self.assertEqual(
        'woof', entity_type.GetFieldFromConfigText('woof').field.field
    )
    self.assertEqual(
        'woof', entity_type.GetFieldFromConfigText('/woof').field.field
    )

    self.assertIsNone(entity_type.GetFieldFromConfigText('/wag'))
    self.assertIsNone(entity_type.GetFieldFromConfigText('wag'))


if __name__ == '__main__':
  absltest.main()
