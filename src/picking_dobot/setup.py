from setuptools import find_packages, setup

package_name = 'picking_dobot'

setup(
    name=package_name,
    version='0.0.0',
    # 수정된 부분: utils 폴더가 빌드되지 않도록 패키지 이름을 직접 지정
    packages=[package_name], 
    
    data_files=[
        ('share/ament_index/resource_index/packages',
            ['resource/' + package_name]),
        ('share/' + package_name, ['package.xml']),
    ],
    install_requires=['setuptools'],
    zip_safe=True,
    maintainer='ssafy',
    maintainer_email='2100238@naver.com',
    description='TODO: Package description',
    license='TODO: License declaration',
    extras_require={
        'test': [
            'pytest',
        ],
    },
    entry_points={
        'console_scripts': [
            'picking_yellow = picking_dobot.picking_yellow:main',
            'control_node = picking_dobot.control_node:main',
            'vision_node = picking_dobot.vision_node:main',
            'test = picking_dobot.test:main',
        ],
    },
)