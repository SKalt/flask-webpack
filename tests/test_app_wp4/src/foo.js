import _ from 'lodash';

export function _foo() {
  console.log(
    _.join(['module', 'foo', 'loaded!'], ' ')
  );
}

export default function foo(){_foo(); console.log('main')}
